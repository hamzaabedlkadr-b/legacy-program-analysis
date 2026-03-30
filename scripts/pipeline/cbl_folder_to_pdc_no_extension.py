#!/usr/bin/env python3
"""
Generate one pdc.json-style file per COBOL source without relying on the
control-flow extension.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List

from cbl_to_pdc_no_extension import build_graph, get_program_id


def collect_cobol_files(root: Path, recursive: bool) -> List[Path]:
    patterns = ["*.CBL", "*.cbl", "*.COB", "*.cob"]
    files: List[Path] = []
    seen = set()
    iterator = root.rglob if recursive else (lambda pat: root.glob(pat))
    for pattern in patterns:
        for path in sorted(iterator(pattern)):
            key = str(path.resolve()).upper()
            if key in seen or not path.is_file():
                continue
            seen.add(key)
            files.append(path)
    return files


def choose_output_name(path: Path, use_program_id: bool) -> str:
    stem = path.stem.upper()
    if not use_program_id:
        return stem
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        raise SystemExit(f"failed to read {path}: {exc}")
    program_id = get_program_id(text)
    return program_id or stem


def write_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Generate one pdc.json-style file per COBOL program without the extension"
    )
    ap.add_argument("--cobol-dir", required=True, help="Folder containing COBOL .CBL/.COB files")
    ap.add_argument("--out-dir", required=True, help="Output folder for generated JSON files")
    ap.add_argument("--use-program-id", action="store_true",
                    help="Use PROGRAM-ID for output filenames when available")
    ap.add_argument("--non-recursive", action="store_true",
                    help="Only scan files directly inside --cobol-dir")
    ap.add_argument("--rankdir", default="LR", help="Graph rankdir stored in each JSON (default: LR)")
    args = ap.parse_args()

    cobol_dir = Path(args.cobol_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    recursive = not args.non_recursive

    if not cobol_dir.exists():
        raise SystemExit(f"COBOL dir not found: {cobol_dir}")
    if not cobol_dir.is_dir():
        raise SystemExit(f"COBOL path is not a directory: {cobol_dir}")

    cobol_files = collect_cobol_files(cobol_dir, recursive)
    if not cobol_files:
        raise SystemExit(f"No COBOL files found in: {cobol_dir}")

    used_names: Dict[str, Path] = {}
    written = 0

    for cobol_path in cobol_files:
        output_name = choose_output_name(cobol_path, args.use_program_id)
        prior = used_names.get(output_name)
        if prior:
            raise SystemExit(
                f"Duplicate output name {output_name}.json for {prior} and {cobol_path}. "
                "Use different filenames or avoid --use-program-id."
            )
        used_names[output_name] = cobol_path

        data = build_graph(cobol_path, graph_name=None, rankdir=args.rankdir)
        out_path = out_dir / f"{output_name}.json"
        write_json(out_path, data)
        written += 1
        print(f"[OK] {cobol_path.name} -> {out_path.name} ({len(data['nodes'])} nodes, {len(data['edges'])} edges)")

    print(f"[DONE] Wrote {written} file(s) to {out_dir}")


if __name__ == "__main__":
    main()
