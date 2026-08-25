#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


def _read_source(path: Path) -> str:
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def extract_copybook_inclusions(path: Path) -> list[dict]:
    division = "UNKNOWN"
    section = "UNKNOWN"
    inclusions: list[dict] = []
    for line_number, raw in enumerate(_read_source(path).splitlines(), start=1):
        indicator = raw[6] if len(raw) > 6 else " "
        if indicator in {"*", "/"}:
            continue
        code = raw[7:] if len(raw) > 7 else raw
        stripped = code.strip()
        if not stripped:
            continue
        division_match = re.match(r"^([A-Z0-9-]+)\s+DIVISION\.", stripped, re.IGNORECASE)
        if division_match:
            division = f"{division_match.group(1).upper()} DIVISION"
            section = "UNKNOWN"
            continue
        section_match = re.match(r"^([A-Z0-9-]+)\s+SECTION\.", stripped, re.IGNORECASE)
        if section_match:
            section = f"{section_match.group(1).upper()} SECTION"
            continue
        copy_match = re.search(r"\bCOPY\s+([A-Z0-9-]+)\b", stripped, re.IGNORECASE)
        if not copy_match:
            continue
        inclusions.append(
            {
                "copybook": copy_match.group(1).upper(),
                "line": line_number,
                "division": division,
                "section": section,
                "statement": stripped,
                "source_file": path.name,
            }
        )
    return inclusions


def main():
    ap = argparse.ArgumentParser(description="Extract architecture.copybooks from rag_documents.json")
    ap.add_argument("--input", required=True, help="Path to rag_documents.json")
    ap.add_argument("--program", required=True, help="Program name to extract")
    ap.add_argument("--output", required=True, help="Output architecture.copybooks.json path")
    ap.add_argument("--source", help="Optional COBOL source used to attach COPY line/division evidence")
    args = ap.parse_args()

    docs = json.loads(Path(args.input).read_text(encoding="utf-8"))
    matches = [d for d in docs if d.get("type") == "architecture.copybooks" and d.get("program") == args.program]
    if not matches:
        raise SystemExit(f"architecture.copybooks not found for program: {args.program}")

    out = matches[0]
    if args.source:
        source = Path(args.source)
        if not source.is_file():
            raise SystemExit(f"COBOL source not found: {source}")
        content = out.setdefault("content", {})
        content["inclusions"] = extract_copybook_inclusions(source)
        out.setdefault("meta", {})["copy_location_source"] = source.name
    Path(args.output).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Wrote {args.output}")


if __name__ == "__main__":
    main()
