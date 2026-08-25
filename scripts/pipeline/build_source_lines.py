"""Publish a physical source-address map for a program.

Semantic retrieval finds meaning, not addresses. A question that names a line
number is asking for a specific place in a file, and an embedding cannot
guarantee it returns that place. This builder emits one record per physical
source line so an exact address can be answered by lookup rather than by
similarity, and so section boundaries, paragraph bodies and literal
occurrences can be resolved against the same map.

Fixed-format COBOL is assumed: columns 1-6 sequence, column 7 indicator,
8-11 Area A, 12-72 Area B, 73-80 identification. Text is preserved exactly as
written; the normalized form is only the code area with runs of whitespace
collapsed, so a caller can match statements without losing the original.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterator

INDICATOR_COLUMN = 7
AREA_A_START = 8
CODE_END = 72

_DIVISION = re.compile(r"^(IDENTIFICATION|ID|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION\b", re.IGNORECASE)
_SECTION = re.compile(r"^([A-Z0-9][A-Z0-9-]*)\s+SECTION\s*\.", re.IGNORECASE)
# A paragraph label sits in Area A and is a bare name followed by a period.
_PARAGRAPH = re.compile(r"^([A-Z0-9][A-Z0-9-]*)\s*\.\s*$", re.IGNORECASE)


def read_text(path: Path) -> list[str]:
    """Read a COBOL member without losing lines to an encoding guess."""
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding).splitlines()
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="latin-1", errors="replace").splitlines()


def code_area(line: str) -> str:
    """Columns 8-72. Outside fixed format this degrades to the whole line."""
    if len(line) > INDICATOR_COLUMN and line[:INDICATOR_COLUMN - 1].strip() == "":
        return line[AREA_A_START - 1:CODE_END]
    if len(line) >= INDICATOR_COLUMN:
        return line[AREA_A_START - 1:CODE_END]
    return line


def indicator_of(line: str) -> str:
    return line[INDICATOR_COLUMN - 1] if len(line) >= INDICATOR_COLUMN else " "


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def in_area_a(line: str) -> bool:
    """True when the code starts in Area A, which is where labels live."""
    area = line[AREA_A_START - 1:CODE_END] if len(line) >= AREA_A_START else ""
    return bool(area) and area[:4].strip() != "" and not area.startswith(" ")


def iter_records(path: Path, program: str) -> Iterator[dict[str, Any]]:
    division: str | None = None
    section: str | None = None
    paragraph: str | None = None

    for number, raw in enumerate(read_text(path), start=1):
        indicator = indicator_of(raw)
        is_comment = indicator in {"*", "/"}
        is_continuation = indicator == "-"
        code = code_area(raw)
        normalized = normalize(code)
        is_blank = not normalized

        if not is_comment and normalized:
            division_match = _DIVISION.match(normalized)
            if division_match:
                division = normalize(normalized.rstrip("."))
                section = None
                # Statements after PROCEDURE DIVISION but before the first label
                # belong to an unnamed paragraph that the analyzers already cite
                # by the program name; matching that keeps addresses joinable to
                # the rule and dataflow artifacts.
                paragraph = program if division.upper().startswith("PROCEDURE") else None
            else:
                section_match = _SECTION.match(normalized)
                if section_match:
                    section = f"{section_match.group(1).upper()} SECTION"
                    paragraph = None
                elif in_area_a(raw):
                    paragraph_match = _PARAGRAPH.match(normalized)
                    if paragraph_match:
                        paragraph = paragraph_match.group(1).upper()

        yield {
            "program": program,
            "source_file": path.name,
            "line": number,
            "text": raw,
            "normalized": normalized,
            "indicator": indicator,
            "is_comment": is_comment,
            "is_continuation": is_continuation,
            "is_blank": is_blank,
            "division": division,
            "section": section,
            "paragraph": paragraph,
            "sha256": hashlib.sha256(raw.encode("utf-8", "replace")).hexdigest()[:16],
        }


def source_members(package: Path) -> list[Path]:
    """The main program plus its copybooks: evidence already cites both."""
    members: list[Path] = []
    for sub in ("cobol", "copybooks"):
        directory = package / sub
        if directory.is_dir():
            members.extend(sorted(p for p in directory.iterdir() if p.is_file()))
    return members


def build(package: Path, program: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    for member in source_members(package):
        member_records = list(iter_records(member, program))
        if not member_records:
            continue
        records.extend(member_records)
        files.append({
            "source_file": member.name,
            "line_count": len(member_records),
            "is_main": member.parent.name == "cobol",
        })
    meta = {
        "program": program,
        "type": "program.source_lines",
        "files": files,
        "line_count": len(records),
        "format": "fixed",
        "limitations": [
            "Physical lines as written; no compiler expansion of COPY members.",
            "Division, section and paragraph are carried forward from the last "
            "marker seen in the same file.",
        ],
    }
    return records, meta


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, type=Path, help="program_packages/<PROGRAM>")
    parser.add_argument("--program", required=True)
    parser.add_argument("--out", required=True, type=Path, help="final_scripts/<PROGRAM>")
    args = parser.parse_args()

    records, meta = build(args.package, args.program)
    if not records:
        print(f"no source members found under {args.package}")
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    jsonl = args.out / "program.source_lines.jsonl"
    with jsonl.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    (args.out / "program.source_lines.meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
    )
    print(f"{args.program}: {meta['line_count']} lines across {len(meta['files'])} file(s) -> {jsonl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
