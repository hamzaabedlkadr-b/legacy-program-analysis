#!/usr/bin/env python3
"""Create a simple text PDF from a Markdown document without dependencies."""

from __future__ import annotations

import argparse
import re
import textwrap
from pathlib import Path


PAGE_WIDTH = 595
PAGE_HEIGHT = 842
LEFT = 54
TOP = 790
LINE_HEIGHT = 13
BODY_SIZE = 10
TITLE_SIZE = 17
HEADING_SIZE = 13
MONO_SIZE = 9


def clean_markdown_line(line: str) -> tuple[str, str]:
    stripped = line.rstrip()
    if not stripped:
        return "", "blank"
    if stripped.startswith("# "):
        return stripped[2:].strip(), "title"
    if stripped.startswith("## "):
        return stripped[3:].strip(), "heading"
    if stripped.startswith("### "):
        return stripped[4:].strip(), "heading"
    if stripped.startswith("- "):
        return "• " + stripped[2:].strip(), "body"
    if stripped.startswith("```"):
        return "", "code_marker"
    stripped = re.sub(r"`([^`]+)`", r"\1", stripped)
    stripped = stripped.replace("**", "")
    return stripped, "body"


def markdown_to_lines(markdown: str) -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []
    in_code = False
    for raw_line in markdown.splitlines():
        line, kind = clean_markdown_line(raw_line)
        if kind == "code_marker":
            in_code = not in_code
            continue
        if in_code:
            output.append((raw_line.rstrip(), "code"))
            continue
        output.append((line, kind))
    return output


def wrap_lines(lines: list[tuple[str, str]]) -> list[tuple[str, str]]:
    wrapped: list[tuple[str, str]] = []
    for line, kind in lines:
        if kind == "blank":
            wrapped.append(("", kind))
            continue
        width = 70 if kind in {"title", "heading"} else 92
        if kind == "code":
            width = 84
        prefix = ""
        subsequent = ""
        if line.startswith("• "):
            prefix = "• "
            subsequent = "  "
            line = line[2:]
        pieces = textwrap.wrap(line, width=width, break_long_words=False, break_on_hyphens=False) or [""]
        for index, piece in enumerate(pieces):
            wrapped.append(((prefix if index == 0 else subsequent) + piece, kind))
    return wrapped


def pdf_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .encode("latin-1", errors="replace")
        .decode("latin-1")
    )


def paginate(lines: list[tuple[str, str]]) -> list[list[tuple[str, str]]]:
    pages: list[list[tuple[str, str]]] = [[]]
    y = TOP
    for line, kind in lines:
        size = TITLE_SIZE if kind == "title" else HEADING_SIZE if kind == "heading" else MONO_SIZE if kind == "code" else BODY_SIZE
        extra = 10 if kind == "title" else 6 if kind == "heading" else 0
        needed = LINE_HEIGHT + extra
        if y - needed < 52:
            pages.append([])
            y = TOP
        pages[-1].append((line, kind))
        y -= needed
    return pages


def page_stream(page: list[tuple[str, str]], page_number: int, total_pages: int) -> str:
    parts = ["BT"]
    y = TOP
    current_font = None
    for line, kind in page:
        if kind == "title":
            font, size = "F1", TITLE_SIZE
            y -= 4
        elif kind == "heading":
            font, size = "F1", HEADING_SIZE
            y -= 3
        elif kind == "code":
            font, size = "F2", MONO_SIZE
        else:
            font, size = "F3", BODY_SIZE
        if current_font != (font, size):
            parts.append(f"/{font} {size} Tf")
            current_font = (font, size)
        if kind == "blank":
            y -= LINE_HEIGHT
            continue
        parts.append(f"1 0 0 1 {LEFT} {y} Tm ({pdf_escape(line)}) Tj")
        y -= LINE_HEIGHT + (7 if kind == "title" else 4 if kind == "heading" else 0)
    parts.append(f"/F3 8 Tf 1 0 0 1 {LEFT} 30 Tm (Page {page_number} of {total_pages}) Tj")
    parts.append("ET")
    return "\n".join(parts)


def write_pdf(pages: list[list[tuple[str, str]]], output: Path) -> None:
    objects: list[bytes] = []

    def add_object(content: str) -> int:
        objects.append(content.encode("latin-1", errors="replace"))
        return len(objects)

    catalog_id = add_object("<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add_object("PLACEHOLDER")
    font_bold_id = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    font_mono_id = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
    font_body_id = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_ids: list[int] = []
    for index, page in enumerate(pages, start=1):
        stream = page_stream(page, index, len(pages))
        stream_id = add_object(f"<< /Length {len(stream.encode('latin-1', errors='replace'))} >>\nstream\n{stream}\nendstream")
        page_id = add_object(
            "<< /Type /Page /Parent 2 0 R "
            f"/MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Resources << /Font << /F1 {font_bold_id} 0 R /F2 {font_mono_id} 0 R /F3 {font_body_id} 0 R >> >> "
            f"/Contents {stream_id} 0 R >>"
        )
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("latin-1")

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as handle:
        handle.write(b"%PDF-1.4\n")
        offsets = [0]
        for object_number, content in enumerate(objects, start=1):
            offsets.append(handle.tell())
            handle.write(f"{object_number} 0 obj\n".encode("ascii"))
            handle.write(content)
            handle.write(b"\nendobj\n")
        xref_offset = handle.tell()
        handle.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        handle.write(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            handle.write(f"{offset:010d} 00000 n \n".encode("ascii"))
        handle.write(
            (
                "trailer\n"
                f"<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
                "startxref\n"
                f"{xref_offset}\n"
                "%%EOF\n"
            ).encode("ascii")
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    markdown = args.input.read_text(encoding="utf-8")
    lines = wrap_lines(markdown_to_lines(markdown))
    pages = paginate(lines)
    write_pdf(pages, args.output)
    print(f"Wrote {args.output} ({len(pages)} pages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
