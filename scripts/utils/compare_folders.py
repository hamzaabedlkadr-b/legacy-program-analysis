#!/usr/bin/env python3
"""
Compare two folders and report which files are exact matches.

The script compares files by relative path under each folder. For every file it
finds, it reports one of these outcomes:
  - MATCH: file exists on both sides and is byte-for-byte identical
  - DIFFERENT: file exists on both sides but content differs
  - LEFT ONLY: file exists only in the left folder
  - RIGHT ONLY: file exists only in the right folder
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Iterable, List


DEFAULT_CHUNK_SIZE = 1024 * 1024


def die(message: str, code: int = 1) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)
    raise SystemExit(code)


def iter_files(root: Path, recursive: bool) -> Iterable[Path]:
    if recursive:
        yield from sorted(path for path in root.rglob("*") if path.is_file())
        return
    yield from sorted(path for path in root.iterdir() if path.is_file())


def build_index(root: Path, recursive: bool) -> Dict[Path, Path]:
    return {path.relative_to(root): path for path in iter_files(root, recursive)}


def files_are_equal(left: Path, right: Path, chunk_size: int = DEFAULT_CHUNK_SIZE) -> bool:
    if left.stat().st_size != right.stat().st_size:
        return False

    with left.open("rb") as left_handle, right.open("rb") as right_handle:
        while True:
            left_chunk = left_handle.read(chunk_size)
            right_chunk = right_handle.read(chunk_size)
            if left_chunk != right_chunk:
                return False
            if not left_chunk:
                return True


def write_report(log_path: Path, lines: List[str]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare two folders and report exact file matches by relative path"
    )
    parser.add_argument("--left", required=True, help="First folder to compare")
    parser.add_argument("--right", required=True, help="Second folder to compare")
    parser.add_argument(
        "--log",
        default="compare_folders.log",
        help="Path to the output log file (default: compare_folders.log)",
    )
    parser.add_argument(
        "--non-recursive",
        action="store_true",
        help="Compare only files directly inside each folder",
    )
    args = parser.parse_args()

    left_root = Path(args.left).resolve()
    right_root = Path(args.right).resolve()
    log_path = Path(args.log).resolve()
    recursive = not args.non_recursive

    if not left_root.exists():
        die(f"left folder not found: {left_root}")
    if not left_root.is_dir():
        die(f"left path is not a folder: {left_root}")
    if not right_root.exists():
        die(f"right folder not found: {right_root}")
    if not right_root.is_dir():
        die(f"right path is not a folder: {right_root}")

    left_index = build_index(left_root, recursive)
    right_index = build_index(right_root, recursive)
    all_relative_paths = sorted(set(left_index) | set(right_index))

    matches = 0
    different = 0
    left_only = 0
    right_only = 0
    report_lines: List[str] = [
        "=" * 72,
        "FOLDER COMPARISON REPORT",
        "=" * 72,
        f"Left folder : {left_root}",
        f"Right folder: {right_root}",
        f"Recursive   : {'yes' if recursive else 'no'}",
        "",
    ]

    for relative_path in all_relative_paths:
        left_file = left_index.get(relative_path)
        right_file = right_index.get(relative_path)

        if left_file and right_file:
            if files_are_equal(left_file, right_file):
                matches += 1
                report_lines.append(f"[MATCH]      {relative_path.as_posix()}")
            else:
                different += 1
                report_lines.append(f"[DIFFERENT]  {relative_path.as_posix()}")
            continue

        if left_file:
            left_only += 1
            report_lines.append(f"[LEFT ONLY]  {relative_path.as_posix()}")
            continue

        right_only += 1
        report_lines.append(f"[RIGHT ONLY] {relative_path.as_posix()}")

    report_lines.extend(
        [
            "",
            "-" * 72,
            "SUMMARY",
            "-" * 72,
            f"Compared on both sides: {matches + different}",
            f"Exact matches         : {matches}",
            f"Different files       : {different}",
            f"Only in left folder   : {left_only}",
            f"Only in right folder  : {right_only}",
            f"Total file entries    : {len(all_relative_paths)}",
        ]
    )

    write_report(log_path, report_lines)

    for line in report_lines:
        print(line)

    print("")
    print(f"[DONE] Report written to {log_path}")


if __name__ == "__main__":
    main()
