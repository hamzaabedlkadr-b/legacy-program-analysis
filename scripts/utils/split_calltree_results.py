import argparse
import shutil
import sys
from pathlib import Path
from typing import Iterable


GENERATED_HEADER = "generated files:"
FAILED_HEADER = "failed files:"
GENERATED_SUFFIX = "_result.csv"
FAILED_SUFFIX = ".cbl"
TEXT_ENCODINGS = ("utf-8", "cp1252", "latin-1")


def die(message: str, code: int = 1) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)
    raise SystemExit(code)


def read_text(path: Path) -> str:
    for encoding in TEXT_ENCODINGS:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    die(f"could not decode text file: {path}")


def unique_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        key = value.upper()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(value)
    return ordered


def parse_summary(summary_path: Path) -> tuple[list[str], list[str]]:
    generated_programs: list[str] = []
    failed_programs: list[str] = []
    section: str | None = None

    for raw_line in read_text(summary_path).splitlines():
        line = raw_line.strip()
        if not line:
            continue

        lowered = line.lower()
        if lowered == GENERATED_HEADER:
            section = "generated"
            continue
        if lowered == FAILED_HEADER:
            section = "failed"
            continue

        if section == "generated":
            program = parse_generated_program(line)
            if program:
                generated_programs.append(program)
        elif section == "failed":
            program = parse_failed_program(line)
            if program:
                failed_programs.append(program)

    return (
        unique_preserve_order(generated_programs),
        unique_preserve_order(failed_programs),
    )


def parse_generated_program(line: str) -> str | None:
    file_name = Path(line).name
    lowered = file_name.lower()
    if not lowered.endswith(GENERATED_SUFFIX):
        return None
    return file_name[: -len(GENERATED_SUFFIX)]


def parse_failed_program(line: str) -> str | None:
    candidate = line
    exit_code_marker = " (exit code"
    marker_index = line.lower().find(exit_code_marker)
    if marker_index != -1:
        candidate = line[:marker_index].rstrip()

    path = Path(candidate)
    if path.suffix.lower() != FAILED_SUFFIX:
        return None
    return path.stem


def build_cbl_index(cbl_root: Path) -> dict[str, list[Path]]:
    if not cbl_root.is_dir():
        die(f"CBL source directory not found: {cbl_root}")

    index: dict[str, list[Path]] = {}
    for path in cbl_root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() != FAILED_SUFFIX:
            continue
        index.setdefault(path.stem.upper(), []).append(path)
    return index


def resolve_program(program: str, cbl_index: dict[str, list[Path]]) -> tuple[Path | None, str | None]:
    candidates = cbl_index.get(program.upper(), [])
    if not candidates:
        return None, "missing"

    expected_name = f"{program}.cbl".lower()
    exact_name_matches = [path for path in candidates if path.name.lower() == expected_name]
    if len(exact_name_matches) == 1:
        return exact_name_matches[0], None
    if len(candidates) == 1:
        return candidates[0], None

    sorted_candidates = sorted(candidates, key=lambda item: str(item).lower())
    return None, "ambiguous: " + ", ".join(str(path) for path in sorted_candidates)


def copy_group(
    programs: Iterable[str],
    cbl_index: dict[str, list[Path]],
    destination_dir: Path,
) -> tuple[list[Path], list[str], list[str]]:
    copied: list[Path] = []
    missing: list[str] = []
    ambiguous: list[str] = []

    destination_dir.mkdir(parents=True, exist_ok=True)

    for program in programs:
        source_path, error = resolve_program(program, cbl_index)
        if source_path is None:
            if error and error.startswith("ambiguous:"):
                ambiguous.append(f"{program}: {error.removeprefix('ambiguous: ')}")
            else:
                missing.append(program)
            continue

        target_path = destination_dir / source_path.name
        shutil.copy2(source_path, target_path)
        copied.append(target_path)

    return copied, missing, ambiguous


def print_group_result(title: str, copied: list[Path], missing: list[str], ambiguous: list[str]) -> None:
    print(f"{title}:")
    print(f"  copied: {len(copied)}")
    print(f"  missing: {len(missing)}")
    print(f"  ambiguous: {len(ambiguous)}")

    if missing:
        print("  missing programs:")
        for program in missing:
            print(f"    {program}")

    if ambiguous:
        print("  ambiguous programs:")
        for entry in ambiguous:
            print(f"    {entry}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Parse a calltree summary text file and copy matching .CBL files "
            "into generated/failed folders."
        )
    )
    parser.add_argument("summary_txt", help="Path to the txt file that contains Generated files / Failed files")
    parser.add_argument("cbl_dir", help="Directory that contains the original .CBL files")
    parser.add_argument("output_dir", help="Directory where 'generated' and 'failed' folders will be created")
    args = parser.parse_args()

    summary_path = Path(args.summary_txt).expanduser().resolve()
    cbl_dir = Path(args.cbl_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    if not summary_path.is_file():
        die(f"summary txt file not found: {summary_path}")

    generated_programs, failed_programs = parse_summary(summary_path)
    cbl_index = build_cbl_index(cbl_dir)

    generated_dir = output_dir / "generated"
    failed_dir = output_dir / "failed"

    generated_copied, generated_missing, generated_ambiguous = copy_group(
        generated_programs,
        cbl_index,
        generated_dir,
    )
    failed_copied, failed_missing, failed_ambiguous = copy_group(
        failed_programs,
        cbl_index,
        failed_dir,
    )

    print(f"Summary file: {summary_path}")
    print(f"CBL source dir: {cbl_dir}")
    print(f"Output dir: {output_dir}")
    print(f"Generated programs found in txt: {len(generated_programs)}")
    print(f"Failed programs found in txt: {len(failed_programs)}")
    print_group_result("generated", generated_copied, generated_missing, generated_ambiguous)
    print_group_result("failed", failed_copied, failed_missing, failed_ambiguous)


if __name__ == "__main__":
    main()
