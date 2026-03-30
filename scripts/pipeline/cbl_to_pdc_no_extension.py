#!/usr/bin/env python3
"""
Generate a pdc_no_extension.json from a COBOL .CBL file.
The output format matches pdc.json:
{
  "graph": {"name": "...", "rankdir": "LR"},
  "nodes": [...],
  "edges": [{"from": "...", "to": "..."}, ...]
}
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


COBOL_KEYWORDS = {
    "END-IF",
    "END-READ",
    "END-EVALUATE",
    "END-PERFORM",
    "END-EXEC",
    "IF",
    "ELSE",
    "EVALUATE",
    "WHEN",
    "PERFORM",
    "GO",
    "GOTO",
    "GO-TO",
    "MOVE",
    "COMPUTE",
    "ADD",
    "SUBTRACT",
    "MULTIPLY",
    "DIVIDE",
    "SET",
    "INITIALIZE",
    "EXEC",
    "CICS",
    "CALL",
    "LINK",
    "XCTL",
    "RETURN",
    "EXIT",
    "STOP",
    "RUN",
    "THEN",
    "UNTIL",
    "VARYING",
    "SEARCH",
    "NEXT",
    "SENTENCE",
    "SECTION",
    "DIVISION",
    "PROCEDURE",
    "DATA",
    "ENVIRONMENT",
    "IDENTIFICATION",
    "SPECIAL-NAMES",
}


PROGRAM_ID_RE = re.compile(r"PROGRAM-ID\.\s*([A-Z0-9-]+)\.", re.IGNORECASE)
PROC_DIV_RE = re.compile(r"^\s*PROCEDURE\s+DIVISION\b", re.IGNORECASE)
PARA_RE = re.compile(r"^\s*([A-Z][A-Z0-9-]{1,30})\.\s*$")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "artifacts" / "intermediate" / "pdc_no_extension.json"


def die(msg: str, code: int = 1) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    raise SystemExit(code)


def get_program_id(text: str) -> Optional[str]:
    m = PROGRAM_ID_RE.search(text)
    return m.group(1).upper() if m else None


def normalize_line_fixed_format(raw: str) -> Tuple[str, bool]:
    """
    COBOL fixed format:
      cols 1-6: sequence
      col 7: indicator
      cols 8-72: code
    Returns (code, is_continuation).
    """
    line = raw.rstrip("\n")
    if not line:
        return "", False
    padded = line + (" " * max(0, 80 - len(line)))
    indicator = padded[6] if len(padded) > 6 else " "
    if indicator in ("*", "/", "D"):
        return "", False
    code = padded[7:72].rstrip()
    is_cont = (indicator == "-")
    return code, is_cont


def strip_inline_comment(code: str) -> str:
    if "*>".upper() in code.upper():
        return code.split("*>", 1)[0].rstrip()
    return code


def read_statements(path: Path) -> List[str]:
    out: List[str] = []
    buf = ""

    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        code, is_cont = normalize_line_fixed_format(raw)
        if not code:
            continue
        code = strip_inline_comment(code)
        if not code:
            continue
        if is_cont and buf:
            buf += " " + code.strip()
            continue
        if buf:
            out.append(buf.strip())
            buf = ""
        buf = code

    if buf:
        out.append(buf.strip())

    return out


def filter_procedure_division(stmts: List[str]) -> List[str]:
    out: List[str] = []
    in_proc = False
    for s in stmts:
        if PROC_DIV_RE.match(s):
            in_proc = True
            continue
        if in_proc:
            out.append(s)
    return out


def is_paragraph_label(stmt: str) -> Optional[str]:
    m = PARA_RE.match(stmt.upper())
    if not m:
        return None
    name = m.group(1).upper()
    if name in COBOL_KEYWORDS:
        return None
    return name


def extract_perform(stmt: str) -> Tuple[Optional[str], Optional[Tuple[str, str]]]:
    s = stmt.upper()

    m = re.search(r"\bPERFORM\b\s+([A-Z0-9-]+)\s+(THRU|THROUGH)\s+([A-Z0-9-]+)", s)
    if m:
        start = m.group(1).upper()
        end = m.group(3).upper()
        return start, (start, end)

    m = re.search(r"\bPERFORM\b\s+([A-Z0-9-]+)\b", s)
    if not m:
        return None, None
    tgt = m.group(1).upper()
    if tgt in {"UNTIL", "VARYING", "TEST"}:
        return None, None
    return tgt, None


def extract_goto_targets(stmt: str) -> List[str]:
    s = stmt.upper()
    if "NEXT SENTENCE" in s:
        return []

    m = re.search(r"\bGO\s+TO\b\s+(.+)", s)
    if not m:
        m = re.search(r"\bGOTO\b\s+(.+)", s)
    if not m:
        return []

    rest = m.group(1)
    rest = rest.split("DEPENDING")[0]
    rest = rest.replace(".", " ")

    targets = []
    for tok in re.findall(r"\b[A-Z][A-Z0-9-]*\b", rest):
        if tok in COBOL_KEYWORDS:
            continue
        targets.append(tok)
    return targets


def add_edge(edges: List[Dict[str, str]], seen: Set[Tuple[str, str]], src: str, tgt: str) -> None:
    key = (src, tgt)
    if key in seen:
        return
    edges.append({"from": src, "to": tgt})
    seen.add(key)


def add_range_edges(
    edges: List[Dict[str, str]],
    seen: Set[Tuple[str, str]],
    order: List[str],
    start: str,
    end: str,
) -> None:
    if start not in order or end not in order:
        return
    i1 = order.index(start)
    i2 = order.index(end)
    if i1 > i2:
        return
    for i in range(i1, i2):
        add_edge(edges, seen, order[i], order[i + 1])


def is_terminal_statement(stmt: str) -> bool:
    s = stmt.strip().upper()
    if not s:
        return False
    if s.startswith("GO TO ") or s.startswith("GOTO "):
        return True
    if s.startswith("STOP RUN") or s.startswith("GOBACK") or s.startswith("EXIT PROGRAM"):
        return True
    if s.startswith("RETURN"):
        return True
    if s.startswith("EXEC CICS") and (" RETURN" in s or " XCTL" in s):
        return True
    return False


def build_graph(cobol_path: Path, graph_name: Optional[str], rankdir: str) -> Dict:
    try:
        text = cobol_path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        die(f"COBOL file not found: {cobol_path}")
    except Exception as exc:
        die(f"failed to read {cobol_path}: {exc}")

    program_id = get_program_id(text) or cobol_path.stem.upper()
    graph_name = graph_name or program_id

    stmts = read_statements(cobol_path)
    proc_stmts = filter_procedure_division(stmts)

    nodes: Set[str] = set()
    order: List[str] = []
    edges: List[Dict[str, str]] = []
    seen_edges: Set[Tuple[str, str]] = set()
    ranges: List[Tuple[str, str]] = []

    paragraphs: Dict[str, List[str]] = {}

    current = program_id
    nodes.add(current)
    order.append(current)
    paragraphs[current] = []

    for stmt in proc_stmts:
        label = is_paragraph_label(stmt)
        if label:
            current = label
            if label not in nodes:
                nodes.add(label)
                order.append(label)
            paragraphs.setdefault(current, [])
            continue
        paragraphs.setdefault(current, []).append(stmt)

    for pname in order:
        for stmt in paragraphs.get(pname, []):
            tgt, rng = extract_perform(stmt)
            if tgt:
                add_edge(edges, seen_edges, pname, tgt)
                nodes.add(tgt)
            if rng:
                ranges.append(rng)

            # Inline PERFORM UNTIL / VARYING loops without explicit paragraph target
            su = stmt.upper()
            if "PERFORM" in su and (" UNTIL " in su or " VARYING " in su) and not tgt:
                add_edge(edges, seen_edges, pname, pname)

            for tgt in extract_goto_targets(stmt):
                add_edge(edges, seen_edges, pname, tgt)
                nodes.add(tgt)

    for start, end in ranges:
        add_range_edges(edges, seen_edges, order, start, end)

    # Add fallthrough edges between sequential paragraphs when not terminated
    for i, pname in enumerate(order[:-1]):
        next_p = order[i + 1]
        stmts_in_para = paragraphs.get(pname, [])
        last_stmt = ""
        for s in reversed(stmts_in_para):
            if s.strip():
                last_stmt = s
                break
        if last_stmt and is_terminal_statement(last_stmt):
            continue
        add_edge(edges, seen_edges, pname, next_p)

    return {
        "graph": {"name": graph_name, "rankdir": rankdir},
        "nodes": sorted(nodes),
        "edges": edges,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="COBOL -> pdc_no_extension.json")
    ap.add_argument("--cobol", required=True, help="Path to COBOL .CBL/.COB file")
    ap.add_argument("--out", default=str(DEFAULT_OUTPUT), help="Output JSON path")
    ap.add_argument("--graph-name", default=None, help="Override graph name")
    ap.add_argument("--rankdir", default="LR", help="Graph rankdir (default: LR)")
    args = ap.parse_args()

    cobol_path = Path(args.cobol)
    out_path = Path(args.out)

    data = build_graph(cobol_path, graph_name=args.graph_name, rankdir=args.rankdir)

    try:
        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        die(f"failed to write {out_path}: {exc}")

    print(f"[OK] Wrote {out_path} with {len(data['nodes'])} nodes and {len(data['edges'])} edges.")


if __name__ == "__main__":
    main()
