#!/usr/bin/env python3
import argparse
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Set
import re


REPORT_RE = re.compile(r"([A-Za-z0-9_-]+)\.json\b", re.IGNORECASE)


def parse_exts(value: str) -> Set[str]:
    exts: Set[str] = set()
    for part in value.split(","):
        item = part.strip()
        if not item:
            continue
        if not item.startswith("."):
            item = "." + item
        exts.add(item.lower())
    return exts


def read_report_text(report_file: str | None) -> str:
    if report_file:
        return Path(report_file).read_text(encoding="utf-8", errors="ignore")
    return sys.stdin.read()


def extract_stems(report_text: str) -> List[str]:
    stems: List[str] = []
    seen: Set[str] = set()
    for match in REPORT_RE.findall(report_text):
        stem = match.upper()
        if stem in seen:
            continue
        seen.add(stem)
        stems.append(stem)
    return stems


def collect_source_index(source_dir: Path, exts: Set[str], recursive: bool) -> Dict[str, List[Path]]:
    index: Dict[str, List[Path]] = {}
    files = source_dir.rglob("*") if recursive else source_dir.glob("*")
    for path in files:
        if not path.is_file():
            continue
        if path.suffix.lower() not in exts:
            continue
        index.setdefault(path.stem.upper(), []).append(path)
    return index


def copy_matches(stems: List[str], source_dir: Path, out_dir: Path, index: Dict[str, List[Path]]) -> tuple[int, List[str], List[str]]:
    copied = 0
    missing: List[str] = []
    ambiguous: List[str] = []

    for stem in stems:
        matches = index.get(stem, [])
        if not matches:
            missing.append(stem)
            continue

        if len(matches) > 1:
            ambiguous.append(f"{stem}: {len(matches)} matches")

        for src in matches:
            rel = src.relative_to(source_dir)
            dst = out_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
            print(f"[OK] copied {src} -> {dst}")

    return copied, missing, ambiguous


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Copy COBOL source files whose stems appear in an invalid DOT report."
    )
    ap.add_argument("--source-dir", required=True, help="Folder containing COBOL source files")
    ap.add_argument("--output-dir", required=True, help="Folder where matching source files will be copied")
    ap.add_argument("--report-file", help="Text file containing the debug report. If omitted, read from stdin")
    ap.add_argument("--source-exts", default=".cbl,.cob", help="Comma-separated source extensions")
    ap.add_argument("--recursive", action="store_true", help="Search source-dir recursively")
    ap.add_argument("--fail-on-missing", action="store_true", help="Exit with code 2 if any report stem is not found")
    args = ap.parse_args()

    source_dir = Path(args.source_dir)
    out_dir = Path(args.output_dir)
    if not source_dir.exists() or not source_dir.is_dir():
        raise SystemExit(f"source dir not found or not a directory: {source_dir}")

    report_text = read_report_text(args.report_file)
    stems = extract_stems(report_text)
    if not stems:
        raise SystemExit("no .json names found in report input")

    source_exts = parse_exts(args.source_exts)
    index = collect_source_index(source_dir, source_exts, args.recursive)
    out_dir.mkdir(parents=True, exist_ok=True)

    copied, missing, ambiguous = copy_matches(stems, source_dir, out_dir, index)

    print(f"[INFO] report stems: {len(stems)}")
    print(f"[INFO] copied source files: {copied}")
    print(f"[INFO] stems not found: {len(missing)}")
    print(f"[INFO] stems with multiple source matches: {len(ambiguous)}")

    if missing:
        print("[DEBUG] Missing source files:")
        for stem in missing:
            print(f"  - {stem}")

    if ambiguous:
        print("[DEBUG] Multiple source matches:")
        for item in ambiguous:
            print(f"  - {item}")

    if args.fail_on_missing and missing:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
