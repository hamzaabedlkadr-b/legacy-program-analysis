#!/usr/bin/env python3
"""
Batch convert DOT control-flow files (stored as .txt/.dot) into pdc.json files.
Each input file produces one JSON file with the same stem in the output folder.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional


EDGE_RE = re.compile(r"<([^>]+)>\s*->\s*<([^>]+)>\s*;")
DIGRAPH_RE = re.compile(r"digraph\s+([A-Za-z0-9_]+)\s*\{", re.IGNORECASE)


def die(msg: str, code: int = 1) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    raise SystemExit(code)


def validate_dot_text(text: str) -> Optional[str]:
    stripped = (text or "").strip()
    if not stripped:
        return "empty file"

    if not DIGRAPH_RE.search(text):
        return "missing 'digraph ... {' header"

    if "}" not in text:
        return "missing closing '}'"

    if not EDGE_RE.search(text):
        return "no edges found in DOT format like <A>-><B>;"

    return None


def parse_dot(text: str) -> Dict:
    err = validate_dot_text(text)
    if err:
        raise ValueError(f"not in dott.txt format: {err}")

    # Graph name: digraph A { ... }
    m = DIGRAPH_RE.search(text)
    graph_name = m.group(1) if m else "G"

    # rankdir=LR (optional)
    m = re.search(r"rankdir\s*=\s*([A-Za-z]+)\s*;", text)
    rankdir = m.group(1) if m else None

    nodes = set()
    edges: List[Dict[str, str]] = []

    for a, b in EDGE_RE.findall(text):
        nodes.add(a)
        nodes.add(b)
        edges.append({"from": a, "to": b})

    return {
        "graph": {"name": graph_name, "rankdir": rankdir},
        "nodes": sorted(nodes),
        "edges": edges,
    }


def iter_files(dot_dir: Path, pattern: str, recursive: bool) -> List[Path]:
    if recursive:
        return sorted(dot_dir.rglob(pattern))
    return sorted(dot_dir.glob(pattern))


def run_dot_to_json(dot_to_json: Path, dot_file: Path, out_path: Path) -> None:
    if not dot_to_json.exists():
        raise FileNotFoundError(f"dot_to_json.py not found: {dot_to_json}")

    text = dot_file.read_text(encoding="utf-8", errors="ignore")
    err = validate_dot_text(text)
    if err:
        raise ValueError(f"not in dott.txt format: {err}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        dott = tmpdir_path / "dott.txt"
        pdc = tmpdir_path / "pdc.json"

        shutil.copyfile(dot_file, dott)
        res = subprocess.run([sys.executable, str(dot_to_json)], cwd=str(tmpdir_path))
        if res.returncode != 0:
            raise RuntimeError(f"dot_to_json.py failed for {dot_file.name}")
        if not pdc.exists():
            raise RuntimeError(f"dot_to_json.py did not produce pdc.json for {dot_file.name}")

        shutil.move(str(pdc), str(out_path))


def main() -> None:
    ap = argparse.ArgumentParser(description="Convert DOT .txt files into pdc.json files")
    ap.add_argument("--dot-dir", required=True, help="Folder containing DOT files (.txt/.dot)")
    ap.add_argument("--out-dir", required=True, help="Output folder for pdc.json files")
    ap.add_argument("--pattern", default="*.txt", help="Glob pattern (default: *.txt)")
    ap.add_argument("--recursive", action="store_true", help="Search recursively")
    ap.add_argument("--dot-to-json", help="Path to dot_to_json.py (uses it if provided)")
    args = ap.parse_args()

    dot_dir = Path(args.dot_dir)
    out_dir = Path(args.out_dir)

    if not dot_dir.exists():
        die(f"dot dir not found: {dot_dir}")
    if not dot_dir.is_dir():
        die(f"dot path is not a directory: {dot_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)

    files = iter_files(dot_dir, args.pattern, args.recursive)
    if not files:
        die(f"no files found in {dot_dir} with pattern {args.pattern}")

    total = 0
    invalid_format: List[str] = []
    failed_other: List[str] = []
    dot_to_json = Path(args.dot_to_json) if args.dot_to_json else None
    for f in files:
        out_path = out_dir / f"{f.stem}.json"
        try:
            if dot_to_json:
                run_dot_to_json(dot_to_json, f, out_path)
                print(f"[OK] {f.name} -> {out_path.name} (via dot_to_json.py)")
            else:
                text = f.read_text(encoding="utf-8", errors="ignore")
                data = parse_dot(text)
                out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                print(
                    f"[OK] {f.name} -> {out_path.name} "
                    f"({len(data['nodes'])} nodes, {len(data['edges'])} edges)"
                )
        except ValueError as exc:
            msg = f"{f.name}: {exc}"
            print(f"[WARN] {msg}")
            invalid_format.append(msg)
            continue
        except Exception as exc:
            msg = f"{f.name}: {exc}"
            print(f"[WARN] failed to convert {f}: {exc}")
            failed_other.append(msg)
            continue
        total += 1

    print(f"[DONE] Wrote {total} file(s) to {out_dir}")
    print(f"[INFO] Invalid dott.txt format: {len(invalid_format)}")
    print(f"[INFO] Other conversion failures: {len(failed_other)}")

    if invalid_format:
        print("[DEBUG] Files not in dott.txt format:")
        for item in invalid_format:
            print(f"  - {item}")

    if failed_other:
        print("[DEBUG] Other failed conversions:")
        for item in failed_other:
            print(f"  - {item}")


if __name__ == "__main__":
    main()
