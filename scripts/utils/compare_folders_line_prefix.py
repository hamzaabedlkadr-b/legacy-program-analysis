#!/usr/bin/env python3
"""
Compare two folders using line-count and line-prefix rules.

Two files are treated as similar when:
  - they exist on both sides at the same relative path
  - they have the same number of lines
  - for each corresponding line, the text before the first comma matches
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


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


def prefix_before_first_comma(line: str) -> str:
    return line.split(",", 1)[0].strip()


def compare_by_line_prefix(left: Path, right: Path, encoding: str) -> Tuple[bool, str]:
    left_lines = left.read_text(encoding=encoding, errors="replace").splitlines()
    right_lines = right.read_text(encoding=encoding, errors="replace").splitlines()

    if len(left_lines) != len(right_lines):
        return False, f"line count mismatch ({len(left_lines)} vs {len(right_lines)})"

    for line_number, (left_line, right_line) in enumerate(zip(left_lines, right_lines), start=1):
        left_prefix = prefix_before_first_comma(left_line)
        right_prefix = prefix_before_first_comma(right_line)
        if left_prefix != right_prefix:
            return (
                False,
                f"line {line_number} prefix mismatch ({left_prefix!r} vs {right_prefix!r})",
            )

    return True, f"{len(left_lines)} line(s) matched before the first comma"


def write_report(log_path: Path, lines: List[str]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compare two folders by relative path, line count, "
            "and the text before the first comma on each line"
        )
    )
    parser.add_argument("--left", required=True, help="First folder to compare")
    parser.add_argument("--right", required=True, help="Second folder to compare")
    parser.add_argument(
        "--log",
        default="compare_folders_line_prefix.log",
        help="Path to the output log file (default: compare_folders_line_prefix.log)",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Text encoding used to read files (default: utf-8)",
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

    similar = 0
    different = 0
    left_only = 0
    right_only = 0
    errors = 0
    report_lines: List[str] = [
        "=" * 72,
        "LINE PREFIX FOLDER COMPARISON REPORT",
        "=" * 72,
        f"Left folder : {left_root}",
        f"Right folder: {right_root}",
        f"Recursive   : {'yes' if recursive else 'no'}",
        f"Encoding    : {args.encoding}",
        "",
    ]

    for relative_path in all_relative_paths:
        left_file = left_index.get(relative_path)
        right_file = right_index.get(relative_path)

        if left_file and right_file:
            try:
                is_similar, detail = compare_by_line_prefix(left_file, right_file, args.encoding)
            except Exception as exc:
                errors += 1
                report_lines.append(f"[ERROR]      {relative_path.as_posix()} ({exc})")
                continue

            if is_similar:
                similar += 1
                report_lines.append(f"[SIMILAR]    {relative_path.as_posix()} ({detail})")
            else:
                different += 1
                report_lines.append(f"[DIFFERENT]  {relative_path.as_posix()} ({detail})")
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
            f"Compared on both sides: {similar + different + errors}",
            f"Similar files         : {similar}",
            f"Different files       : {different}",
            f"Read errors           : {errors}",
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
