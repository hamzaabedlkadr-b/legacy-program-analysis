#!/usr/bin/env python3
"""Prepare the root input layout used by run_fixed_input.py.

Required output layout:

  <output-root>/PROGRAM/
    PROGRAM.CBL
    PROGRAM_result.csv        or PROGRAM_result.txt
    PROGRAM_controlflow.json
    copybooks/

The script starts from separate folders for COBOL sources, MAPA/result files,
control-flow JSON files, and copybooks. It writes JSON, CSV, and Markdown
reports so missing or ambiguous inputs are visible after the run.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


COBOL_SUFFIXES = {".cbl", ".cob", ".cobol"}
RESULT_SUFFIXES = {".csv", ".txt"}
COPYBOOK_SUFFIXES = {"", ".cpy", ".copy"}
COPY_RE = re.compile(
    r"^\s*(?!\*)\s*(?:[A-Z0-9_-]+\s+)?COPY\s+['\"]?([A-Z0-9_$#@-]+)",
    re.IGNORECASE,
)
PROGRAM_ID_RE = re.compile(r"\bPROGRAM-ID\.\s*([A-Z0-9_-]+)", re.IGNORECASE)
SYSTEM_COPYBOOKS = {"DFHAID", "DFHBMSCA", "SQLCA", "SQLDA"}
TEXT_ENCODINGS = ("utf-8", "cp1252", "latin-1")


@dataclass
class FileCopy:
    source: str | None = None
    target: str | None = None
    status: str = "missing"
    extra_matches: list[str] = field(default_factory=list)


@dataclass
class ProgramReport:
    program: str
    source_stem: str
    output_dir: str
    status: str = "OK"
    cbl: FileCopy = field(default_factory=FileCopy)
    result: FileCopy = field(default_factory=FileCopy)
    controlflow: FileCopy = field(default_factory=FileCopy)
    copybooks_mode: str = "all"
    copybooks_copied: int = 0
    copybooks_missing: list[str] = field(default_factory=list)
    copybooks_ambiguous: dict[str, list[str]] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cbl-dir", required=True, type=Path, help="Folder containing .CBL/.COB/.COBOL files.")
    parser.add_argument(
        "--controlflow-dir",
        required=True,
        type=Path,
        help="Folder containing PROGRAM_controlflow.json files.",
    )
    parser.add_argument(
        "--result-path",
        required=True,
        type=Path,
        help="Folder containing PROGRAM_result.csv/.txt files, or one result file for a single program.",
    )
    parser.add_argument(
        "--copybooks-dir",
        required=True,
        type=Path,
        help=(
            "Folder containing copybook files. Copybooks may be .cpy files or files without an extension. "
            "This may be the same folder as --cbl-dir; .CBL/.COB/.COBOL files are ignored as copybooks."
        ),
    )
    parser.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Destination root, for example input.",
    )
    parser.add_argument(
        "--copybooks-mode",
        choices=("all", "referenced", "empty"),
        default="all",
        help=(
            "Copy all copybooks, only COPY-referenced copybooks, or just create an empty copybooks folder. "
            "Copybook discovery keeps only .cpy/.copy/extensionless files and ignores COBOL source files. "
            "Referenced mode matches both NAME.cpy and extensionless NAME files. "
            "Default: all."
        ),
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search input folders recursively and preserve copybook subfolders.",
    )
    parser.add_argument(
        "--use-program-id",
        action="store_true",
        help="Use PROGRAM-ID from each COBOL file for folder/file names instead of the file stem.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Do not overwrite same-named files already present in the output folder.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show the report without creating or copying files.")
    parser.add_argument(
        "--report-stem",
        default="organize_report",
        help="Base name for report files written under --output-root.",
    )
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Exit with code 2 when any program is missing required files.",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    for encoding in TEXT_ENCODINGS:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


def iter_files(root: Path, recursive: bool) -> Iterable[Path]:
    pattern = "**/*" if recursive else "*"
    return (path for path in root.glob(pattern) if path.is_file())


def collect_files(root: Path, recursive: bool, suffixes: set[str] | None = None) -> list[Path]:
    files = sorted(iter_files(root, recursive), key=lambda item: str(item).lower())
    if suffixes is None:
        return files
    return [path for path in files if path.suffix.lower() in suffixes]


def collect_copybook_files(root: Path, recursive: bool) -> list[Path]:
    return [
        path
        for path in collect_files(root, recursive)
        if path.suffix.lower() in COPYBOOK_SUFFIXES
        and path.suffix.lower() not in COBOL_SUFFIXES
    ]


def resolve_dir(path: Path, label: str) -> Path:
    path = path.expanduser().resolve()
    if not path.is_dir():
        raise SystemExit(f"{label} is not a folder: {path}")
    return path


def resolve_result_path(path: Path) -> Path:
    path = path.expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"--result-path does not exist: {path}")
    if path.is_file() and path.suffix.lower() not in RESULT_SUFFIXES:
        raise SystemExit(f"--result-path file must be .csv or .txt: {path}")
    if not path.is_file() and not path.is_dir():
        raise SystemExit(f"--result-path is not a file or folder: {path}")
    return path


def program_name(cbl: Path, use_program_id: bool) -> str:
    if use_program_id:
        match = PROGRAM_ID_RE.search(read_text(cbl))
        if match:
            return match.group(1).upper()
    return cbl.stem.upper()


def referenced_copybooks(cbl: Path) -> list[str]:
    names: set[str] = set()
    for line in read_text(cbl).splitlines():
        match = COPY_RE.search(line)
        if not match:
            continue
        name = match.group(1).rstrip(".").upper()
        if name and name not in SYSTEM_COPYBOOKS:
            names.add(name)
    return sorted(names)


def build_index(files: Iterable[Path]) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for path in files:
        for key in {path.stem.upper(), path.name.upper()}:
            index.setdefault(key, []).append(path)
    return index


def unique(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    ordered: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered.append(path)
    return ordered


def result_files_from_path(result_path: Path, recursive: bool) -> list[Path]:
    if result_path.is_file():
        return [result_path]
    return collect_files(result_path, recursive, RESULT_SUFFIXES)


def match_result(program: str, stem: str, result_path: Path, result_index: dict[str, list[Path]], cbl_count: int) -> list[Path]:
    if result_path.is_file():
        file_stem = result_path.stem.upper()
        exact_stems = {f"{program}_RESULT", f"{stem.upper()}_RESULT"}
        if file_stem in exact_stems or cbl_count == 1:
            return [result_path]
        return []

    keys = [
        f"{program}_RESULT.CSV",
        f"{program}_RESULT.TXT",
        f"{stem.upper()}_RESULT.CSV",
        f"{stem.upper()}_RESULT.TXT",
        f"{program}_RESULT",
        f"{stem.upper()}_RESULT",
    ]
    matches: list[Path] = []
    for key in keys:
        matches.extend(result_index.get(key.upper(), []))
    return unique(path for path in matches if path.suffix.lower() in RESULT_SUFFIXES)


def match_controlflow(program: str, stem: str, cfg_index: dict[str, list[Path]]) -> list[Path]:
    keys = [
        f"{program}_CONTROLFLOW.JSON",
        f"{stem.upper()}_CONTROLFLOW.JSON",
        f"{program}_CONTROLFLOW",
        f"{stem.upper()}_CONTROLFLOW",
        f"{program}_CFG.JSON",
        f"{stem.upper()}_CFG.JSON",
        f"{program}_CFG",
        f"{stem.upper()}_CFG",
        f"{program}.JSON",
        f"{stem.upper()}.JSON",
        program,
        stem.upper(),
    ]
    matches: list[Path] = []
    for key in keys:
        matches.extend(cfg_index.get(key.upper(), []))
    return unique(path for path in matches if path.suffix.lower() == ".json")


def choose_preferred(paths: list[Path], preferred_suffixes: tuple[str, ...]) -> tuple[Path | None, list[Path]]:
    if not paths:
        return None, []
    ordered = sorted(
        paths,
        key=lambda path: (
            preferred_suffixes.index(path.suffix.lower())
            if path.suffix.lower() in preferred_suffixes
            else len(preferred_suffixes),
            str(path).lower(),
        ),
    )
    return ordered[0], ordered[1:]


def copy_file(src: Path, dest: Path, dry_run: bool, skip_existing: bool) -> str:
    if dry_run:
        return "would_copy"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and skip_existing:
        return "exists"
    shutil.copy2(src, dest)
    return "copied"


def copy_all_copybooks(
    copybook_files: list[Path],
    copybooks_dir: Path,
    dest_copybooks: Path,
    dry_run: bool,
    skip_existing: bool,
) -> tuple[int, list[str]]:
    copied = 0
    notes: list[str] = []
    for src in copybook_files:
        relative = src.relative_to(copybooks_dir)
        status = copy_file(src, dest_copybooks / relative, dry_run, skip_existing)
        if status in {"copied", "would_copy", "exists"}:
            copied += 1
    if not copybook_files:
        notes.append("No copybook files were found in the copybooks folder.")
    return copied, notes


def copy_referenced_copybooks(
    cbl: Path,
    copybooks_dir: Path,
    copy_index: dict[str, list[Path]],
    dest_copybooks: Path,
    dry_run: bool,
    skip_existing: bool,
) -> tuple[int, list[str], dict[str, list[str]]]:
    copied = 0
    missing: list[str] = []
    ambiguous: dict[str, list[str]] = {}

    for name in referenced_copybooks(cbl):
        keys = [
            name,
            f"{name}.CPY",
            f"{name}.COPY",
            f"{name}.COB",
            f"{name}.CBL",
        ]
        matches = unique(path for key in keys for path in copy_index.get(key.upper(), []))
        if not matches:
            missing.append(name)
            continue
        if len(matches) > 1:
            ambiguous[name] = [str(path) for path in matches]
            continue

        src = matches[0]
        relative = src.relative_to(copybooks_dir)
        status = copy_file(src, dest_copybooks / relative, dry_run, skip_existing)
        if status in {"copied", "would_copy", "exists"}:
            copied += 1

    return copied, missing, ambiguous


def create_copybooks_folder(dest_copybooks: Path, dry_run: bool) -> None:
    if not dry_run:
        dest_copybooks.mkdir(parents=True, exist_ok=True)


def status_from_report(report: ProgramReport) -> str:
    if "duplicate COBOL program name" in report.missing:
        return "FAIL"
    if "result" in report.missing or "controlflow" in report.missing:
        return "FAIL"
    if report.copybooks_missing or report.copybooks_ambiguous or report.result.extra_matches or report.controlflow.extra_matches:
        return "WARN"
    if any("No copybook files" in note for note in report.notes):
        return "WARN"
    return "OK"


def organize_program(
    cbl: Path,
    program: str,
    args: argparse.Namespace,
    paths: dict[str, Path],
    indexes: dict[str, dict[str, list[Path]]],
    result_path: Path,
    result_file_count: int,
    all_copybook_files: list[Path],
    used_results: set[Path],
    used_controlflows: set[Path],
) -> ProgramReport:
    output_dir = paths["output_root"] / program
    report = ProgramReport(
        program=program,
        source_stem=cbl.stem,
        output_dir=str(output_dir),
        copybooks_mode=args.copybooks_mode,
    )

    cbl_target = output_dir / f"{program}.CBL"
    report.cbl = FileCopy(
        source=str(cbl),
        target=str(cbl_target),
        status=copy_file(cbl, cbl_target, args.dry_run, args.skip_existing),
    )

    result_matches = match_result(program, cbl.stem, result_path, indexes["result"], result_file_count)
    result_src, result_extra = choose_preferred(result_matches, (".csv", ".txt"))
    if result_src is None:
        report.missing.append("result")
    else:
        result_target = output_dir / f"{program}_result{result_src.suffix.lower()}"
        report.result = FileCopy(
            source=str(result_src),
            target=str(result_target),
            status=copy_file(result_src, result_target, args.dry_run, args.skip_existing),
            extra_matches=[str(path) for path in result_extra],
        )
        if result_extra:
            report.notes.append(f"Multiple result files matched; selected {result_src.name}.")
        used_results.add(result_src.resolve())

    cfg_matches = match_controlflow(program, cbl.stem, indexes["controlflow"])
    cfg_src, cfg_extra = choose_preferred(cfg_matches, (".json",))
    if cfg_src is None:
        report.missing.append("controlflow")
    else:
        cfg_target = output_dir / f"{program}_controlflow.json"
        report.controlflow = FileCopy(
            source=str(cfg_src),
            target=str(cfg_target),
            status=copy_file(cfg_src, cfg_target, args.dry_run, args.skip_existing),
            extra_matches=[str(path) for path in cfg_extra],
        )
        if cfg_extra:
            report.notes.append(f"Multiple controlflow files matched; selected {cfg_src.name}.")
        used_controlflows.add(cfg_src.resolve())

    dest_copybooks = output_dir / "copybooks"
    create_copybooks_folder(dest_copybooks, args.dry_run)
    if args.copybooks_mode == "all":
        copied, notes = copy_all_copybooks(
            all_copybook_files,
            paths["copybooks_dir"],
            dest_copybooks,
            args.dry_run,
            args.skip_existing,
        )
        report.copybooks_copied = copied
        report.notes.extend(notes)
    elif args.copybooks_mode == "referenced":
        copied, missing, ambiguous = copy_referenced_copybooks(
            cbl,
            paths["copybooks_dir"],
            indexes["copybooks"],
            dest_copybooks,
            args.dry_run,
            args.skip_existing,
        )
        report.copybooks_copied = copied
        report.copybooks_missing = missing
        report.copybooks_ambiguous = ambiguous
        report.notes.append("System copybooks DFHAID, DFHBMSCA, SQLCA, and SQLDA are ignored in referenced mode.")
    else:
        report.notes.append("Created copybooks folder without copying copybook files.")

    report.status = status_from_report(report)
    return report


def duplicate_report(cbl: Path, program: str, output_root: Path) -> ProgramReport:
    report = ProgramReport(
        program=program,
        source_stem=cbl.stem,
        output_dir=str(output_root / program),
        status="FAIL",
    )
    report.cbl.source = str(cbl)
    report.missing.append("duplicate COBOL program name")
    report.notes.append("Multiple COBOL files resolve to this program name; no files were copied for this entry.")
    return report


def write_json_report(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def csv_row(report: ProgramReport) -> dict[str, str | int]:
    return {
        "program": report.program,
        "status": report.status,
        "output_dir": report.output_dir,
        "cbl_source": report.cbl.source or "",
        "cbl_status": report.cbl.status,
        "result_source": report.result.source or "",
        "result_status": report.result.status,
        "controlflow_source": report.controlflow.source or "",
        "controlflow_status": report.controlflow.status,
        "copybooks_mode": report.copybooks_mode,
        "copybooks_copied": report.copybooks_copied,
        "missing": "; ".join(report.missing),
        "missing_copybooks": "; ".join(report.copybooks_missing),
        "ambiguous_copybooks": "; ".join(report.copybooks_ambiguous),
        "notes": "; ".join(report.notes),
    }


def write_csv_report(path: Path, reports: list[ProgramReport]) -> None:
    rows = [csv_row(report) for report in reports]
    fieldnames = list(rows[0].keys()) if rows else list(csv_row(ProgramReport("", "", "")).keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown_report(path: Path, payload: dict) -> None:
    summary = payload["summary"]
    lines = [
        "# Program Input Organization Report",
        "",
        f"- Created at UTC: {payload['created_at_utc']}",
        f"- Output root: `{payload['output_root']}`",
        f"- Programs: {summary['program_count']}",
        f"- OK: {summary['ok']}",
        f"- WARN: {summary['warn']}",
        f"- FAIL: {summary['fail']}",
        "",
        "| Program | Status | Missing | Copybooks | Notes |",
        "| --- | --- | --- | ---: | --- |",
    ]

    for item in payload["programs"]:
        missing_parts = (
            item["missing"]
            + [f"copybook:{name}" for name in item["copybooks_missing"]]
            + [f"ambiguous-copybook:{name}" for name in item["copybooks_ambiguous"]]
        )
        missing = ", ".join(missing_parts)
        notes = "; ".join(item["notes"])
        lines.append(
            f"| {item['program']} | {item['status']} | {missing or '-'} | "
            f"{item['copybooks_copied']} | {notes or '-'} |"
        )

    unmatched = payload["unmatched_inputs"]
    if unmatched["results"] or unmatched["controlflow"]:
        lines.extend(["", "## Unmatched Input Files", ""])
        if unmatched["results"]:
            lines.append("Result files not matched to a COBOL program:")
            lines.extend(f"- `{path}`" for path in unmatched["results"])
            lines.append("")
        if unmatched["controlflow"]:
            lines.append("Control-flow JSON files not matched to a COBOL program:")
            lines.extend(f"- `{path}`" for path in unmatched["controlflow"])
            lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build_payload(
    args: argparse.Namespace,
    paths: dict[str, Path],
    reports: list[ProgramReport],
    result_files: list[Path],
    controlflow_files: list[Path],
    used_results: set[Path],
    used_controlflows: set[Path],
) -> dict:
    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dry_run": args.dry_run,
        "inputs": {
            "cbl_dir": str(paths["cbl_dir"]),
            "controlflow_dir": str(paths["controlflow_dir"]),
            "result_path": str(paths["result_path"]),
            "copybooks_dir": str(paths["copybooks_dir"]),
        },
        "output_root": str(paths["output_root"]),
        "options": {
            "copybooks_mode": args.copybooks_mode,
            "recursive": args.recursive,
            "use_program_id": args.use_program_id,
            "skip_existing": args.skip_existing,
        },
        "summary": {
            "program_count": len(reports),
            "ok": sum(1 for report in reports if report.status == "OK"),
            "warn": sum(1 for report in reports if report.status == "WARN"),
            "fail": sum(1 for report in reports if report.status == "FAIL"),
        },
        "programs": [asdict(report) for report in reports],
        "unmatched_inputs": {
            "results": [str(path) for path in result_files if path.resolve() not in used_results],
            "controlflow": [str(path) for path in controlflow_files if path.resolve() not in used_controlflows],
        },
    }


def print_summary(payload: dict) -> None:
    summary = payload["summary"]
    print(
        f"Programs: {summary['program_count']} | "
        f"OK: {summary['ok']} | WARN: {summary['warn']} | FAIL: {summary['fail']}"
    )
    for item in payload["programs"]:
        missing = ", ".join(item["missing"])
        if item["copybooks_missing"]:
            missing = (missing + ", " if missing else "") + f"{len(item['copybooks_missing'])} copybook(s)"
        suffix = f" ({missing})" if missing else ""
        print(f"[{item['status']}] {item['program']}{suffix}")


def main() -> int:
    args = parse_args()
    paths = {
        "cbl_dir": resolve_dir(args.cbl_dir, "--cbl-dir"),
        "controlflow_dir": resolve_dir(args.controlflow_dir, "--controlflow-dir"),
        "result_path": resolve_result_path(args.result_path),
        "copybooks_dir": resolve_dir(args.copybooks_dir, "--copybooks-dir"),
        "output_root": args.output_root.expanduser().resolve(),
    }

    cbl_files = collect_files(paths["cbl_dir"], args.recursive, COBOL_SUFFIXES)
    if not cbl_files:
        raise SystemExit(f"No COBOL files found in {paths['cbl_dir']}")

    result_files = result_files_from_path(paths["result_path"], args.recursive)
    controlflow_files = collect_files(paths["controlflow_dir"], args.recursive, {".json"})
    all_copybook_files = collect_copybook_files(paths["copybooks_dir"], args.recursive)

    result_index = build_index(result_files)
    controlflow_index = build_index(controlflow_files)
    copybook_index = build_index(all_copybook_files)
    indexes = {"result": result_index, "controlflow": controlflow_index, "copybooks": copybook_index}

    program_by_cbl = {cbl: program_name(cbl, args.use_program_id) for cbl in cbl_files}
    duplicate_programs = {
        program
        for program in program_by_cbl.values()
        if list(program_by_cbl.values()).count(program) > 1
    }

    used_results: set[Path] = set()
    used_controlflows: set[Path] = set()
    reports: list[ProgramReport] = []
    for cbl in cbl_files:
        program = program_by_cbl[cbl]
        if program in duplicate_programs:
            reports.append(duplicate_report(cbl, program, paths["output_root"]))
            continue
        reports.append(
            organize_program(
                cbl,
                program,
                args,
                paths,
                indexes,
                paths["result_path"],
                len(cbl_files),
                all_copybook_files,
                used_results,
                used_controlflows,
            )
        )

    payload = build_payload(args, paths, reports, result_files, controlflow_files, used_results, used_controlflows)

    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        paths["output_root"].mkdir(parents=True, exist_ok=True)
        json_path = paths["output_root"] / f"{args.report_stem}.json"
        csv_path = paths["output_root"] / f"{args.report_stem}.csv"
        md_path = paths["output_root"] / f"{args.report_stem}.md"
        write_json_report(json_path, payload)
        write_csv_report(csv_path, reports)
        write_markdown_report(md_path, payload)
        print_summary(payload)
        print(f"Reports: {json_path}, {csv_path}, {md_path}")

    if args.fail_on_missing and payload["summary"]["fail"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
