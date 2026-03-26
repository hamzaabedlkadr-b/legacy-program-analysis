#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Iterable, Set


def parse_exts(value: str) -> Set[str]:
    exts = set()
    for part in value.split(","):
        p = part.strip()
        if not p:
            continue
        if not p.startswith("."):
            p = "." + p
        exts.add(p.lower())
    return exts


def collect_stems(folder: Path, exts: Set[str], recursive: bool) -> Set[str]:
    stems: Set[str] = set()
    iterator: Iterable[Path]
    iterator = folder.rglob("*") if recursive else folder.glob("*")

    for p in iterator:
        if not p.is_file():
            continue
        if p.suffix.lower() not in exts:
            continue
        stems.add(p.stem.upper())
    return stems


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Compare source folder and generated folder by filename stem."
    )
    ap.add_argument("--source-dir", required=True, help="Folder with source files (e.g. COBOL)")
    ap.add_argument("--generated-dir", required=True, help="Folder with generated files (e.g. CCF JSON)")
    ap.add_argument(
        "--source-exts",
        default=".cbl,.cob",
        help="Comma-separated source extensions (default: .cbl,.cob)",
    )
    ap.add_argument(
        "--generated-exts",
        default=".json",
        help="Comma-separated generated extensions (default: .json)",
    )
    ap.add_argument("--recursive", action="store_true", help="Scan folders recursively")
    ap.add_argument(
        "--write-missing",
        help="Optional output file to write missing source stems (txt or json by extension)",
    )
    ap.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Exit with code 2 if any source stem is missing in generated folder",
    )
    args = ap.parse_args()

    source_dir = Path(args.source_dir)
    generated_dir = Path(args.generated_dir)

    if not source_dir.exists() or not source_dir.is_dir():
        raise SystemExit(f"Source dir not found or not a directory: {source_dir}")
    if not generated_dir.exists() or not generated_dir.is_dir():
        raise SystemExit(f"Generated dir not found or not a directory: {generated_dir}")

    source_exts = parse_exts(args.source_exts)
    generated_exts = parse_exts(args.generated_exts)

    source_stems = collect_stems(source_dir, source_exts, args.recursive)
    generated_stems = collect_stems(generated_dir, generated_exts, args.recursive)

    missing = sorted(source_stems - generated_stems)
    extra = sorted(generated_stems - source_stems)

    print(f"[INFO] source files matched: {len(source_stems)}")
    print(f"[INFO] generated files matched: {len(generated_stems)}")
    print(f"[INFO] missing generated for source stems: {len(missing)}")
    print(f"[INFO] extra generated without source stem: {len(extra)}")

    if missing:
        print("[MISSING]")
        for s in missing:
            print(f"  - {s}")

    if extra:
        print("[EXTRA]")
        for s in extra:
            print(f"  - {s}")

    if args.write_missing:
        out_path = Path(args.write_missing)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.suffix.lower() == ".json":
            payload = {"missing": missing}
            out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        else:
            out_path.write_text("\n".join(missing), encoding="utf-8")
        print(f"[OK] wrote missing list: {out_path}")

    if args.fail_on_missing and missing:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
