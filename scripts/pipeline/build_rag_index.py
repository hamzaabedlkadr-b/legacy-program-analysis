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
    parser.add_argument(
        "--profile",
        choices=("full", "compact"),
        default="full",
        help=(
            "Indexing profile. full indexes every supported artifact. compact skips "
            "known aggregate duplicates and trims evidence-heavy docs for lower token use."
        ),
    )
    parser.add_argument(
        "--global-docs-dir",
        type=Path,
        help="Optional global RAG map folder. Defaults to <out-root>/_global/rag_maps when present.",
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


def has_json_children(path: Path) -> bool:
    return path.is_dir() and any(child.is_file() and child.suffix.lower() == ".json" for child in path.iterdir())


def should_skip_compact_source(path: Path, program_dir: Path) -> bool:
    artifacts_dir = program_dir / "artifacts"
    if path.parent != artifacts_dir:
        return False
    if path.name == "dataflow.used_variables.json" and has_json_children(artifacts_dir / "dataflow.variable"):
        return True
    if path.name == "program.comments.json" and has_json_children(artifacts_dir / "program.comments"):
        return True
    return False


def iter_source_files(program_dir: Path, include_input_rag: bool, profile: str = "full") -> list[Path]:
    files: list[Path] = []
    artifacts_dir = program_dir / "artifacts"
    if artifacts_dir.is_dir():
        files.extend(sorted(artifacts_dir.glob("*.json")))
        files.extend(sorted(artifacts_dir.glob("*/*.json")))
    files = [path for path in files if not path.stem.startswith("optimization.constants")]
    if profile == "compact":
        files = [path for path in files if not should_skip_compact_source(path, program_dir)]

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


def iter_global_source_files(global_docs_dir: Path | None) -> list[Path]:
    if not global_docs_dir or not global_docs_dir.is_dir():
        return []
    files = [
        path
        for path in sorted(global_docs_dir.rglob("*.json"))
        if path.is_file()
        and path.name not in {"global_maps_manifest.json"}
        and not path.name.endswith(".rag_documents.json")
    ]
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


def normalize_call_type(value: Any) -> str:
    raw = scalar_to_text(value).upper()
    if "XCTL" in raw:
        return "XCTL"
    if "LINK" in raw:
        return "LINK"
    if "CALL" in raw:
        return "CALL"
    return raw


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


def nested_scalar(doc: dict[str, Any], *keys: str) -> str:
    current: Any = doc
    for key in keys:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
    return scalar_to_text(current)


def coverage_dimension(doc_type: str) -> str:
    if doc_type.startswith("global."):
        return "cross_program"
    if doc_type in {"integration.conflicts"}:
        return "conflict_report"
    if doc_type.startswith("quality."):
        return "quality_confidence"
    if doc_type in {"controlflow.cfg", "workflow", "paragraph_logic", "screen.interaction"}:
        return "deep_logic"
    return "static_inventory"


def call_metadata(doc: dict[str, Any], doc_type: str, program: str, path: Path) -> dict[str, str]:
    if not (
        doc_type.startswith("architecture.call")
        or doc_type in {"external_program_calls", "call_contract"}
        or doc_type.startswith("cobol_rekt.call_contract")
        or doc_type.startswith("cobol_rekt.external_program_calls")
    ):
        return {}

    content = doc.get("content") if isinstance(doc.get("content"), dict) else {}
    meta = doc.get("meta") or doc.get("metadata")
    meta = meta if isinstance(meta, dict) else {}
    evidence = doc.get("evidence") if isinstance(doc.get("evidence"), dict) else {}

    target = (
        scalar_to_text(doc.get("target"))
        or nested_scalar(content, "target")
        or nested_scalar(meta, "target")
        or nested_scalar(evidence, "target")
    )
    call_type = (
        normalize_call_type(doc.get("call_type"))
        or normalize_call_type(nested_scalar(content, "call_type"))
        or normalize_call_type(nested_scalar(content, "type"))
        or normalize_call_type(nested_scalar(meta, "call_type"))
        or normalize_call_type(nested_scalar(evidence, "type"))
    )

    if not target and doc_type == "architecture.call":
        parts = path.stem.split(".")
        if len(parts) >= 4:
            call_type = call_type or normalize_call_type(parts[-2])
            target = parts[-1]

    if not target:
        return {}
    call_type = call_type or "CALL"
    return {
        "entity_type": "call",
        "entity_key": f"{program}|{target.upper()}|{call_type}",
        "target": target.upper(),
        "call_type": call_type,
    }


def flatten_value(value: Any, prefix: str = "", depth: int = 0, list_limit: int = 120) -> list[str]:
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
            lines.extend(flatten_value(value[key], child_prefix, depth + 1, list_limit))
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
        for index, item in enumerate(complex_items[:list_limit]):
            child_prefix = f"{prefix}[{index}]" if prefix else f"item[{index}]"
            lines.extend(flatten_value(item, child_prefix, depth + 1, list_limit))
        if len(complex_items) > list_limit:
            label = prefix or "items"
            lines.append(f"{label}: ... {len(complex_items) - list_limit} more complex items not expanded")
        return lines

    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return [f"{prefix}: {text}" if prefix else text]


def compact_ws(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def compact_list(value: Any, limit: int) -> Any:
    if isinstance(value, list) and len(value) > limit:
        return value[:limit] + [{"omitted_items": len(value) - limit}]
    return value


def compact_evidence(evidence: Any, limit: int) -> Any:
    if not isinstance(evidence, dict):
        return evidence
    compacted: dict[str, Any] = {}
    for key, value in evidence.items():
        if isinstance(value, list):
            compacted[key] = compact_list(value, limit)
        else:
            compacted[key] = value
    return compacted


def compact_document_for_profile(doc: dict[str, Any], doc_type: str, profile: str) -> dict[str, Any]:
    if profile != "compact":
        return doc

    if doc_type == "dataflow.variable":
        compacted = dict(doc)
        content = dict(compacted.get("content") or {})
        if "evidence" in content:
            content["evidence"] = compact_evidence(content["evidence"], 8)
        compacted["content"] = content
        return compacted

    if doc_type == "architecture.unused_copybooks":
        compacted = dict(doc)
        content = doc.get("content")
        if not isinstance(content, dict):
            return compacted
        status_summary = []
        for item in content.get("copybook_status") or []:
            if not isinstance(item, dict):
                continue
            evidence = item.get("evidence")
            status_summary.append(
                {
                    "copybook": item.get("copybook"),
                    "status": item.get("status"),
                    "evidence_count": len(evidence) if isinstance(evidence, list) else 0,
                }
            )
        compacted["content"] = {
            "copybooks_total": content.get("copybooks_total"),
            "classified": content.get("classified"),
            "referenced_copybooks": content.get("referenced_copybooks"),
            "needs_review_count": content.get("needs_review_count"),
            "needs_review_copybooks": content.get("needs_review_copybooks"),
            "unused_copybooks_proven": content.get("unused_copybooks_proven"),
            "copybook_status_summary": status_summary,
        }
        return compacted

    return doc


def document_text(
    doc: dict[str, Any],
    program: str,
    doc_type: str,
    *,
    list_limit: int = 120,
    evidence_line_limit: int = 80,
) -> tuple[str, str]:
    title = scalar_to_text(doc.get("title")) or f"{program} {doc_type}"
    parts = [f"Program: {program}", f"Type: {doc_type}", f"Title: {title}"]

    embedding_text = scalar_to_text(doc.get("embedding_text"))
    if embedding_text:
        parts.append(f"Embedding: {embedding_text}")

    content = doc.get("content")
    if content is not None:
        content_lines = flatten_value(content, "content", list_limit=list_limit)
        if content_lines:
            parts.append("Content:\n" + "\n".join(content_lines))

    meta = doc.get("meta") or doc.get("metadata")
    if meta:
        meta_lines = flatten_value(meta, "meta", list_limit=list_limit)
        if meta_lines:
            parts.append("Metadata:\n" + "\n".join(meta_lines))

    evidence = doc.get("evidence")
    if evidence:
        evidence_lines = flatten_value(evidence, "evidence", list_limit=list_limit)
        if evidence_lines:
            parts.append("Evidence:\n" + "\n".join(evidence_lines[:evidence_line_limit]))

    if not embedding_text and content is None:
        parts.append("Document:\n" + "\n".join(flatten_value(doc, list_limit=list_limit)))

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


def source_relative_path(path: Path, base_root: Path) -> str:
    try:
        return path.relative_to(base_root).as_posix()
    except ValueError:
        return path.as_posix()


def add_json_source_file(
    path: Path,
    default_program: str,
    base_root: Path,
    records: list[dict[str, Any]],
    invalid_files: list[dict[str, str]],
    by_program: Counter[str],
    by_type: Counter[str],
    program_types: dict[str, Counter[str]],
    max_chars: int,
    overlap: int,
    profile: str,
) -> tuple[int, int]:
    try:
        data = load_json(path)
    except Exception as exc:
        invalid_files.append({"path": str(path), "error": str(exc)})
        return 1, 0

    source_docs = 0
    rel_path = source_relative_path(path, base_root)
    docs = expand_json_documents(data)
    for json_index, item in enumerate(docs):
        source_docs += 1
        program = scalar_to_text(item.get("program")) or default_program
        program = program.upper()
        doc_type = normalize_type(item, path)
        index_item = compact_document_for_profile(item, doc_type, profile)
        title, text = document_text(
            index_item,
            program,
            doc_type,
            list_limit=40 if profile == "compact" else 120,
            evidence_line_limit=30 if profile == "compact" else 80,
        )
        source_id = scalar_to_text(item.get("id"))
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
                    "chunk_type": doc_type,
                    "source_system": "mapa_hamza",
                    "source_chunk_type": doc_type,
                    "coverage_dimension": coverage_dimension(doc_type),
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
            record["metadata"].update(call_metadata(item, doc_type, program, path))
            records.append(record)
            by_program[program] += 1
            by_type[doc_type] += 1
            program_types[program][doc_type] += 1
    return 1, source_docs


def build_index(
    out_root: Path,
    out_dir: Path,
    include_input_rag: bool,
    max_chars: int,
    overlap: int,
    global_docs_dir: Path | None = None,
    profile: str = "full",
) -> dict[str, Any]:
    programs_dir = resolve_programs_dir(out_root)
    output_root = programs_dir.parent
    if global_docs_dir is None:
        candidate = output_root / "_global" / "rag_maps"
        global_docs_dir = candidate if candidate.is_dir() else None
    records: list[dict[str, Any]] = []
    invalid_files: list[dict[str, str]] = []
    source_file_count = 0
    source_doc_count = 0
    global_source_file_count = 0
    global_source_doc_count = 0
    by_program: Counter[str] = Counter()
    by_type: Counter[str] = Counter()
    program_types: dict[str, Counter[str]] = defaultdict(Counter)

    for program_dir in iter_program_dirs(programs_dir):
        program = program_dir.name.upper()
        for path in iter_source_files(program_dir, include_input_rag, profile):
            files_added, docs_added = add_json_source_file(
                path,
                default_program=program,
                base_root=output_root,
                records=records,
                invalid_files=invalid_files,
                by_program=by_program,
                by_type=by_type,
                program_types=program_types,
                max_chars=max_chars,
                overlap=overlap,
                profile=profile,
            )
            source_file_count += files_added
            source_doc_count += docs_added

    for path in iter_global_source_files(global_docs_dir):
        files_added, docs_added = add_json_source_file(
            path,
            default_program="__GLOBAL__",
            base_root=output_root,
            records=records,
            invalid_files=invalid_files,
            by_program=by_program,
            by_type=by_type,
            program_types=program_types,
            max_chars=max_chars,
            overlap=overlap,
            profile=profile,
        )
        source_file_count += files_added
        source_doc_count += docs_added
        global_source_file_count += files_added
        global_source_doc_count += docs_added

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

    real_program_count = len([program for program in by_program if program != "__GLOBAL__"])
    manifest = {
        "out_root": str(out_root),
        "programs_dir": str(programs_dir),
        "global_docs_dir": str(global_docs_dir) if global_docs_dir else None,
        "out_dir": str(out_dir),
        "profile": profile,
        "source_files": source_file_count,
        "source_documents": source_doc_count,
        "global_source_files": global_source_file_count,
        "global_source_documents": global_source_doc_count,
        "indexed_documents": len(records),
        "program_count": real_program_count,
        "record_group_count": len(by_program),
        "global_indexed_documents": by_program.get("__GLOBAL__", 0),
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
        f"- Profile: {profile}",
        f"- Programs: {manifest['program_count']}",
        f"- Record groups: {manifest['record_group_count']}",
        f"- Global indexed docs/chunks: {manifest['global_indexed_documents']}",
        f"- Source files: {source_file_count}",
        f"- Source documents: {source_doc_count}",
        f"- Global source files: {global_source_file_count}",
        f"- Global source documents: {global_source_doc_count}",
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
        global_docs_dir=args.global_docs_dir,
        profile=args.profile,
    )
    print(f"[OK] Indexed {manifest['indexed_documents']} RAG documents/chunks")
    print(f"[OK] JSONL: {manifest['files']['jsonl']}")
    print(f"[OK] Manifest: {args.out_dir / 'rag_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
