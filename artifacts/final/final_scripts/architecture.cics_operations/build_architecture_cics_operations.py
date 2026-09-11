#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


PARAGRAPH_RE = re.compile(r"^([A-Z0-9][A-Z0-9-]*)\.\s*$", re.IGNORECASE)
COPY_RE = re.compile(r"\bCOPY\s+([A-Z0-9-]+)\s*\.", re.IGNORECASE)
CICS_RE = re.compile(r"\bEXEC\s+CICS\s+([A-Z0-9-]+)\b", re.IGNORECASE)
OPTION_RE = re.compile(
    r"\b([A-Z][A-Z0-9-]*)\s*\(\s*([^()]*(?:\([^()]*\)[^()]*)*)\s*\)",
    re.IGNORECASE,
)
RESOURCE_OPTIONS = {"MAP", "MAPSET", "QUEUE", "FILE", "TRANSID", "PROGRAM"}
NON_PARAGRAPHS = {"END-EXEC", "END-IF", "EJECT", "EXIT", "SKIP1", "SKIP2", "SKIP3"}


def make_id(text: str) -> str:
    return hashlib.blake2b(text.encode("utf-8"), digest_size=8).hexdigest()


def fixed_code(raw: str) -> str:
    """Return the fixed-format code area and discard comment/debug lines."""
    padded = raw.rstrip("\n") + " " * max(0, 80 - len(raw.rstrip("\n")))
    indicator = padded[6]
    if indicator in {"*", "/", "D", "d"}:
        return ""
    return padded[7:72].rstrip()


def structured_options(statement: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Parse CICS option operands once during analysis.

    RAG consumers can filter resources and option roles without reparsing the
    raw statement or relying on embedding similarity.
    """
    options: list[dict[str, str]] = []
    resources: list[dict[str, str]] = []
    for match in OPTION_RE.finditer(statement):
        name = match.group(1).upper()
        raw_value = " ".join(match.group(2).split())
        value = raw_value.strip().strip("'\"")
        option = {
            "name": name,
            "value": value,
            "raw_value": raw_value,
            "value_kind": (
                "literal"
                if raw_value[:1] in {"'", '"'} and raw_value[-1:] == raw_value[:1]
                else "identifier"
            ),
        }
        options.append(option)
        if name in RESOURCE_OPTIONS:
            resources.append({"resource_type": name, "resource": value})
    return options, resources


def scan_source(
    path: Path,
    *,
    initial_paragraph: str = "",
    included_at_line: int | None = None,
) -> tuple[list[dict[str, Any]], list[tuple[str, str, int]]]:
    operations: list[dict[str, Any]] = []
    copy_includes: list[tuple[str, str, int]] = []
    paragraph = initial_paragraph
    buffer: list[str] = []
    start_line = 0

    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
    ):
        code = fixed_code(raw)
        if not code:
            continue

        paragraph_match = PARAGRAPH_RE.fullmatch(code)
        if paragraph_match:
            candidate = paragraph_match.group(1).upper()
            if candidate not in NON_PARAGRAPHS:
                paragraph = candidate

        copy_match = COPY_RE.search(code)
        if copy_match:
            copy_includes.append((copy_match.group(1).upper(), paragraph, line_number))

        if not buffer and CICS_RE.search(code) is None:
            continue
        if not buffer:
            start_line = line_number
        buffer.append(code.strip())
        statement = re.sub(r"\s+", " ", " ".join(buffer)).strip()
        if "END-EXEC" not in statement.upper():
            continue

        command_match = CICS_RE.search(statement)
        if command_match:
            command = command_match.group(1).upper()
            options, resources = structured_options(statement)
            operation = {
                "id": make_id(f"{path}|{start_line}|{statement}"),
                "command": command,
                "paragraph": paragraph or "unknown",
                "source_file": path.name,
                "source_path": str(path),
                "line_start": start_line,
                "line_end": line_number,
                "statement": statement,
                "options": options,
                "resources": resources,
            }
            if included_at_line is not None:
                operation["included_at_line"] = included_at_line
            operations.append(operation)
        buffer = []
        start_line = 0

    return operations, copy_includes


def resolve_copybook(copy_dir: Path, name: str) -> Path | None:
    wanted = name.upper()
    candidates = [copy_dir / name, copy_dir / f"{name}.CPY", copy_dir / f"{name}.cpy"]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    if copy_dir.is_dir():
        for candidate in copy_dir.iterdir():
            if candidate.is_file() and candidate.stem.upper() == wanted:
                return candidate
    return None


def build(cobol: Path, copy_dir: Path, program: str) -> dict[str, Any]:
    operations, copy_includes = scan_source(cobol)
    scanned_copybooks: set[tuple[str, str, int]] = set()
    for name, paragraph, include_line in copy_includes:
        key = (name, paragraph, include_line)
        if key in scanned_copybooks:
            continue
        scanned_copybooks.add(key)
        copybook = resolve_copybook(copy_dir, name)
        if copybook is None:
            continue
        copy_operations, _ = scan_source(
            copybook,
            initial_paragraph=paragraph,
            included_at_line=include_line,
        )
        operations.extend(copy_operations)

    operations.sort(
        key=lambda item: (
            int(item.get("included_at_line") or item.get("line_start") or 0),
            str(item.get("source_file", "")),
            int(item.get("line_start") or 0),
        )
    )
    commands = sorted({str(item["command"]) for item in operations})
    paragraph_names = sorted({str(item["paragraph"]) for item in operations})
    embedding = (
        f"{program} executes CICS commands {', '.join(commands)}. "
        f"Paragraphs: {', '.join(paragraph_names)}."
    )
    return {
        "id": make_id(f"{program}|architecture.cics_operations"),
        "type": "architecture.cics_operations",
        "program": program,
        "title": f"{program} source-backed CICS operations",
        "embedding_text": embedding,
        "content": {
            "commands": commands,
            "operations": operations,
        },
        "meta": {
            "source_files": sorted({str(item["source_path"]) for item in operations}),
            "counts": {
                "commands": len(commands),
                "operations": len(operations),
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build source-backed architecture.cics_operations.json"
    )
    parser.add_argument("--cobol", required=True, type=Path)
    parser.add_argument("--copy-dir", required=True, type=Path)
    parser.add_argument("--program", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    payload = build(args.cobol, args.copy_dir, args.program.upper())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] Wrote {args.output}")


if __name__ == "__main__":
    main()
