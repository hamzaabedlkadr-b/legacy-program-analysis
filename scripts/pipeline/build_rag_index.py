#!/usr/bin/env python3
"""Build a clean RAG ingestion bundle from per-program pipeline outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect per-program JSON artifacts into vector-DB ready RAG documents."
    )
    parser.add_argument(
        "--out-root",
        required=True,
        type=Path,
        help="Pipeline output root. Can be the folder containing programs/ or programs/ itself.",
    )
    parser.add_argument(
        "--out-dir",
        required=True,
        type=Path,
        help="Destination folder for rag_documents.jsonl, rag_documents.json, and manifests.",
    )
    parser.add_argument(
        "--max-text-chars",
        type=int,
        default=12000,
        help="Maximum text size per indexed document chunk.",
    )
    parser.add_argument(
        "--overlap-chars",
        type=int,
        default=600,
        help="Character overlap between chunks when a document is split.",
    )
    parser.add_argument(
        "--skip-input-rag",
        action="store_true",
        help="Skip each program's inputs/rag_documents.json business-rule docs.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def stable_hash(*parts: Any, length: int = 16) -> str:
    raw = "\n".join(str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:length]


def resolve_programs_dir(out_root: Path) -> Path:
    if (out_root / "programs").is_dir():
        return out_root / "programs"
    if out_root.is_dir() and any((child / "artifacts").is_dir() for child in out_root.iterdir() if child.is_dir()):
        return out_root
    raise SystemExit(f"Could not find programs output folder under: {out_root}")


def iter_program_dirs(programs_dir: Path) -> list[Path]:
    return sorted(child for child in programs_dir.iterdir() if child.is_dir())


def iter_source_files(program_dir: Path, include_input_rag: bool) -> list[Path]:
    files: list[Path] = []
    artifacts_dir = program_dir / "artifacts"
    if artifacts_dir.is_dir():
        files.extend(sorted(artifacts_dir.glob("*.json")))
        files.extend(sorted(artifacts_dir.glob("*/*.json")))

    input_rag = program_dir / "inputs" / "rag_documents.json"
    if include_input_rag and input_rag.is_file():
        files.append(input_rag)

    seen: set[str] = set()
    unique: list[Path] = []
    for path in files:
        key = str(path.resolve()).lower()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def source_kind(path: Path) -> str:
    if path.parent.name == "inputs":
        return path.stem
    if path.parent.name == "artifacts":
        return path.stem
    return path.parent.name


def normalize_type(doc: dict[str, Any], path: Path) -> str:
    value = doc.get("type")
    if isinstance(value, str) and value.strip():
        doc_type = value.strip()
        if path.parent.name == "inputs" and path.name == "rag_documents.json":
            return f"{doc_type}.rag"
        return doc_type
    return source_kind(path).replace("_", ".")


def scalar_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value.strip()
    return ""


def flatten_value(value: Any, prefix: str = "", depth: int = 0) -> list[str]:
    if depth > 5:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
        return [f"{prefix}: {text}" if prefix else text]

    scalar = scalar_to_text(value)
    if scalar:
        return [f"{prefix}: {scalar}" if prefix else scalar]

    lines: list[str] = []
    if isinstance(value, dict):
        for key in sorted(value.keys(), key=str):
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            lines.extend(flatten_value(value[key], child_prefix, depth + 1))
        return lines

    if isinstance(value, list):
        simple_items: list[str] = []
        complex_items: list[Any] = []
        for item in value:
            item_text = scalar_to_text(item)
            if item_text:
                simple_items.append(item_text)
            else:
                complex_items.append(item)
        if simple_items:
            label = prefix or "items"
            lines.append(f"{label}: {', '.join(simple_items)}")
        for index, item in enumerate(complex_items[:120]):
            child_prefix = f"{prefix}[{index}]" if prefix else f"item[{index}]"
            lines.extend(flatten_value(item, child_prefix, depth + 1))
        if len(complex_items) > 120:
            label = prefix or "items"
            lines.append(f"{label}: ... {len(complex_items) - 120} more complex items not expanded")
        return lines

    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return [f"{prefix}: {text}" if prefix else text]


def compact_ws(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def document_text(doc: dict[str, Any], program: str, doc_type: str) -> tuple[str, str]:
    title = scalar_to_text(doc.get("title")) or f"{program} {doc_type}"
    parts = [f"Program: {program}", f"Type: {doc_type}", f"Title: {title}"]

    embedding_text = scalar_to_text(doc.get("embedding_text"))
    if embedding_text:
        parts.append(f"Embedding: {embedding_text}")

    content = doc.get("content")
    if content is not None:
        content_lines = flatten_value(content, "content")
        if content_lines:
            parts.append("Content:\n" + "\n".join(content_lines))

    meta = doc.get("meta") or doc.get("metadata")
    if meta:
        meta_lines = flatten_value(meta, "meta")
        if meta_lines:
            parts.append("Metadata:\n" + "\n".join(meta_lines))

    evidence = doc.get("evidence")
    if evidence:
        evidence_lines = flatten_value(evidence, "evidence")
        if evidence_lines:
            parts.append("Evidence:\n" + "\n".join(evidence_lines[:80]))

    if not embedding_text and content is None:
        parts.append("Document:\n" + "\n".join(flatten_value(doc)))

    return title, compact_ws("\n\n".join(parts))


def chunk_text(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    if max_chars <= 0 or len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    start = 0
    overlap = max(0, min(overlap_chars, max_chars // 3))
    while start < len(text):
        end = min(len(text), start + max_chars)
        if end < len(text):
            window = text[start:end]
            break_at = max(window.rfind("\n"), window.rfind(". "), window.rfind("; "))
            if break_at > max_chars * 0.65:
                end = start + break_at + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def expand_json_documents(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def build_index(out_root: Path, out_dir: Path, include_input_rag: bool, max_chars: int, overlap: int) -> dict[str, Any]:
    programs_dir = resolve_programs_dir(out_root)
    records: list[dict[str, Any]] = []
    invalid_files: list[dict[str, str]] = []
    source_file_count = 0
    source_doc_count = 0
    by_program: Counter[str] = Counter()
    by_type: Counter[str] = Counter()
    program_types: dict[str, Counter[str]] = defaultdict(Counter)

    for program_dir in iter_program_dirs(programs_dir):
        program = program_dir.name.upper()
        for path in iter_source_files(program_dir, include_input_rag):
            source_file_count += 1
            try:
                data = load_json(path)
            except Exception as exc:
                invalid_files.append({"path": str(path), "error": str(exc)})
                continue

            rel_path = path.relative_to(programs_dir.parent).as_posix()
            docs = expand_json_documents(data)
            for json_index, doc in enumerate(docs):
                source_doc_count += 1
                doc_type = normalize_type(doc, path)
                title, text = document_text(doc, program, doc_type)
                source_id = scalar_to_text(doc.get("id"))
                chunks = chunk_text(text, max_chars, overlap)
                chunk_count = len(chunks)
                for chunk_index, chunk in enumerate(chunks):
                    record_id = stable_hash(program, rel_path, json_index, source_id, chunk_index)
                    record = {
                        "id": record_id,
                        "program": program,
                        "type": doc_type,
                        "title": title,
                        "text": chunk,
                        "metadata": {
                            "program": program,
                            "type": doc_type,
                            "title": title,
                            "source_file": rel_path,
                            "source_kind": source_kind(path),
                            "source_id": source_id,
                            "json_index": json_index,
                            "chunk_index": chunk_index,
                            "chunk_count": chunk_count,
                            "content_hash": stable_hash(chunk, length=24),
                        },
                    }
                    records.append(record)
                    by_program[program] += 1
                    by_type[doc_type] += 1
                    program_types[program][doc_type] += 1

    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "rag_documents.jsonl"
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    save_json(out_dir / "rag_documents.json", records)

    program_index = [
        {
            "program": program,
            "document_count": by_program[program],
            "types": dict(sorted(program_types[program].items())),
        }
        for program in sorted(by_program)
    ]
    save_json(out_dir / "program_index.json", program_index)

    manifest = {
        "out_root": str(out_root),
        "programs_dir": str(programs_dir),
        "out_dir": str(out_dir),
        "source_files": source_file_count,
        "source_documents": source_doc_count,
        "indexed_documents": len(records),
        "program_count": len(by_program),
        "by_program": dict(sorted(by_program.items())),
        "by_type": dict(sorted(by_type.items())),
        "invalid_files": invalid_files,
        "files": {
            "jsonl": str(jsonl_path),
            "json": str(out_dir / "rag_documents.json"),
            "program_index": str(out_dir / "program_index.json"),
        },
    }
    save_json(out_dir / "rag_manifest.json", manifest)

    md_lines = [
        "# RAG Index Manifest",
        "",
        f"- Programs: {manifest['program_count']}",
        f"- Source files: {source_file_count}",
        f"- Source documents: {source_doc_count}",
        f"- Indexed documents/chunks: {len(records)}",
        f"- Invalid JSON files: {len(invalid_files)}",
        "",
        "| Program | Indexed Docs | Top Types |",
        "|---|---:|---|",
    ]
    for item in program_index:
        top_types = sorted(item["types"].items(), key=lambda kv: (-kv[1], kv[0]))[:8]
        top_text = ", ".join(f"{name}={count}" for name, count in top_types)
        md_lines.append(f"| {item['program']} | {item['document_count']} | {top_text} |")
    (out_dir / "rag_manifest.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    return manifest


def main() -> int:
    args = parse_args()
    manifest = build_index(
        out_root=args.out_root,
        out_dir=args.out_dir,
        include_input_rag=not args.skip_input_rag,
        max_chars=args.max_text_chars,
        overlap=args.overlap_chars,
    )
    print(f"[OK] Indexed {manifest['indexed_documents']} RAG documents/chunks")
    print(f"[OK] JSONL: {manifest['files']['jsonl']}")
    print(f"[OK] Manifest: {args.out_dir / 'rag_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
