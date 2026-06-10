#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple


def make_id(text: str) -> str:
    return hashlib.blake2b(text.encode("utf-8"), digest_size=8).hexdigest()


def normalize_line_fixed_format(raw: str) -> Tuple[str, bool]:
    """
    Normalize a single COBOL source line (fixed format):
      cols 1-6: sequence
      col 7: indicator
      cols 8-72: code
    Returns (code, is_continuation)
    """
    line = raw.rstrip("\n")
    if not line:
        return "", False

    padded = line + (" " * max(0, 80 - len(line)))
    indicator = padded[6] if len(padded) > 6 else " "
    if indicator in ("*", "/"):
        return "", False

    code = padded[7:72].rstrip()
    is_cont = (indicator == "-")
    return code, is_cont


def iter_exec_cics_statements(path: Path) -> List[str]:
    stmts = []
    current = []
    in_exec = False

    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        code, is_cont = normalize_line_fixed_format(raw)
        if not code:
            continue

        up = code.upper()
        if "EXEC CICS" in up and not in_exec:
            in_exec = True
            current = [code]
            if "END-EXEC" in up:
                stmts.append(" ".join(current))
                current = []
                in_exec = False
            continue

        if in_exec:
            current.append(code)
            if "END-EXEC" in up:
                stmts.append(" ".join(current))
                current = []
                in_exec = False

    return stmts


def extract_maps(exec_stmts: List[str]) -> List[Dict]:
    """
    Extract SEND/RECEIVE MAP navigation details from EXEC CICS statements.
    """
    maps: Dict[Tuple[str, str], Dict] = {}
    map_re = re.compile(r"MAP\s*\(\s*['\"]?([A-Z0-9-]+)['\"]?\s*\)", re.IGNORECASE)
    mapset_re = re.compile(r"MAPSET\s*\(\s*['\"]?([A-Z0-9-]+)['\"]?\s*\)", re.IGNORECASE)

    for stmt in exec_stmts:
        su = stmt.upper()
        if "SEND" not in su and "RECEIVE" not in su:
            continue

        op = "SEND" if " SEND " in f" {su} " else "RECEIVE"
        m = map_re.search(stmt)
        if not m:
            continue
        map_name = m.group(1).upper()
        ms = mapset_re.search(stmt)
        mapset = ms.group(1).upper() if ms else ""

        key = (map_name, mapset)
        entry = maps.get(key)
        if not entry:
            entry = {
                "map": map_name,
                "mapset": mapset,
                "operations": set(),
                "options": set(),
                "evidence": [],
            }
            maps[key] = entry

        entry["operations"].add(op)
        for opt in ("ERASE", "CURSOR", "DATAONLY"):
            if opt in su:
                entry["options"].add(opt)
        entry["evidence"].append(stmt.strip())

    out = []
    for (_, _), v in sorted(maps.items()):
        out.append({
            "map": v["map"],
            "mapset": v["mapset"],
            "operations": sorted(v["operations"]),
            "options": sorted(v["options"]),
            "evidence": v["evidence"],
        })
    return out


def extract_ui_actions(edges: List[Dict]) -> Tuple[List[Dict], List[str]]:
    """
    Extract UI navigation actions based on EIBAID/DFH* conditions in CFG edges.
    """
    actions = []
    keys = set()
    eib_re = re.compile(r"EIBAID\s*=\s*([A-Z0-9-]+)", re.IGNORECASE)
    dfh_re = re.compile(r"DFH[A-Z0-9]+", re.IGNORECASE)

    for e in edges:
        cond = e.get("condition")
        if not cond:
            continue
        cu = cond.upper()
        if "EIBAID" not in cu and "DFH" not in cu:
            continue

        key = None
        other_keys = []

        if "EIBAID" in cu and "NOT" in cu:
            key = "OTHER"
            other_keys = sorted({k.upper() for k in dfh_re.findall(cu)})
        else:
            m = eib_re.search(cu)
            if m:
                key = m.group(1).upper()
                keys.add(key)
            else:
                key = "UNKNOWN"

        actions.append({
            "context": e.get("from"),
            "trigger": cond,
            "key": key,
            "other_keys": other_keys,
            "target": e.get("to"),
            "edge_type": e.get("type"),
            "evidence": e.get("evidence"),
        })

    return actions, sorted(keys)


def main():
    ap = argparse.ArgumentParser(description="Build ui.cics.navigation.json from COBOL + enriched CFG")
    ap.add_argument("--cobol", required=True, help="Path to COBOL .CBL file")
    ap.add_argument("--enriched", required=True, help="Path to pdc_enriched.json")
    ap.add_argument("--program", required=True, help="Program name")
    ap.add_argument("--out", required=True, help="Output ui.cics.navigation.json path")
    args = ap.parse_args()

    cobol_path = Path(args.cobol)
    enriched = json.loads(Path(args.enriched).read_text(encoding="utf-8"))
    edges = enriched.get("edges", [])

    exec_stmts = iter_exec_cics_statements(cobol_path)
    maps = extract_maps(exec_stmts)
    actions, keys = extract_ui_actions(edges)

    embedding_parts = []
    if keys:
        embedding_parts.append(
            "Keys: " + ", ".join([f"{k} -> {next((a['target'] for a in actions if a['key']==k), '')}".strip()
                                  for k in keys])
        )
    if maps:
        embedding_parts.append(
            "Maps: " + ", ".join([f"{m['map']}/{m['mapset']} ({'/'.join(m['operations'])})" for m in maps])
        )

    embedding_text = f"CICS UI navigation for {args.program}. " + " ".join(embedding_parts)

    screens = []
    for m in maps:
        if m.get("map") and m.get("mapset"):
            screens.append(f"{m['map']}/{m['mapset']}")
        elif m.get("map"):
            screens.append(m["map"])
    screens = sorted(dict.fromkeys(screens))

    doc = {
        "id": make_id(f"{args.program}|ui.cics.navigation"),
        "type": "ui.cics.navigation",
        "program": args.program,
        "title": f"{args.program} CICS UI navigation",
        "embedding_text": embedding_text.strip(),
        "content": {
            "actions": actions,
            "maps": maps,
            "screens": screens,
        },
        "meta": {
            "source_files": [str(cobol_path), str(Path(args.enriched))],
            "counts": {
                "actions": len(actions),
                "keys": len(keys),
                "maps": len(maps),
            },
        },
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Wrote {out_path}")


if __name__ == "__main__":
    main()
