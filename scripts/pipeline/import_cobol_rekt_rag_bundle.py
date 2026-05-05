"""Import a cobol-rekt knowledge-base_rag bundle as external evidence.

This script is intentionally additive. It never edits artifacts/final/final_scripts.
It copies the current final_scripts into artifacts/combined/final_scripts, then adds
integration artifacts derived from a cobol-rekt knowledge-base_rag bundle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")


def stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:16]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def display_path(path: Path, base: Path | None = None) -> str:
    try:
        resolved = path.resolve()
        if base is not None:
            return resolved.relative_to(base.resolve()).as_posix()
    except ValueError:
        pass
    except OSError:
        pass
    return path.name


def resolve_repo_path(value: str | None, *, required: bool = False) -> Path | None:
    if not value:
        if required:
            raise ValueError("missing required path")
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def resolve_bundle_path(path: Path) -> Path:
    path = path.resolve()
    candidates = [path, path / "knowledge-base_rag"]
    for candidate in candidates:
        if (candidate / "manifest.json").is_file() and (candidate / "chunks").is_dir():
            return candidate
    raise FileNotFoundError(
        f"No cobol-rekt knowledge-base_rag bundle found at {path}. "
        "Expected manifest.json and chunks/."
    )


def artifact_path(root: Path, artifact_type: str, filename: str | None = None) -> Path:
    return root / artifact_type / (filename or f"{artifact_type}.json")


def load_chunks(bundle: Path) -> list[dict[str, Any]]:
    chunks_dir = bundle / "chunks"
    chunk_files = sorted(
        path
        for path in chunks_dir.glob("*.json")
        if path.name not in {"chunks_manifest.json", "bm25_index.json"}
    )
    chunks: list[dict[str, Any]] = []
    for path in chunk_files:
        payload = read_json(path)
        metadata = payload.get("metadata") or {}
        chunk_type = metadata.get("chunk_type") or payload.get("chunk_type") or "unknown"
        chunk_id = payload.get("id") or metadata.get("id") or path.stem
        chunks.append(
            {
                "path": path,
                "source_file": str(path.relative_to(bundle)),
                "id": str(chunk_id),
                "type": str(chunk_type),
                "text": payload.get("text") or payload.get("content") or "",
                "metadata": metadata,
                "payload": payload,
                "sha256": sha256_file(path),
            }
        )
    return chunks


def preview(text: str, limit: int = 500) -> str:
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def chunk_ref(chunk: dict[str, Any], *, text_limit: int = 500) -> dict[str, Any]:
    metadata = chunk["metadata"]
    return {
        "chunk_id": chunk["id"],
        "chunk_type": chunk["type"],
        "source_file": chunk["source_file"],
        "title": metadata.get("title"),
        "program": metadata.get("program"),
        "paragraph": metadata.get("paragraph"),
        "variable": metadata.get("variable"),
        "target": metadata.get("target"),
        "source_line": metadata.get("source_line"),
        "text_preview": preview(chunk["text"], text_limit),
        "sha256": chunk["sha256"],
    }


def read_optional_json(path: Path) -> Any | None:
    if not path.is_file():
        return None
    return read_json(path)


def copy_baseline(final_scripts_root: Path, out_root: Path) -> None:
    if not final_scripts_root.is_dir():
        raise FileNotFoundError(f"final_scripts root not found: {final_scripts_root}")
    if final_scripts_root.resolve() == out_root.resolve():
        raise ValueError("out-root must not be the same as final-scripts-root")
    out_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(final_scripts_root, out_root, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))


def extract_call_contracts(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    contracts = []
    for chunk in chunks:
        metadata = chunk["metadata"]
        contracts.append(
            {
                "target": metadata.get("target"),
                "command": metadata.get("command") or metadata.get("call_type"),
                "paragraph": metadata.get("paragraph"),
                "source_line": metadata.get("source_line"),
                "target_source": metadata.get("target_source"),
                "commarea": metadata.get("commarea"),
                "length": metadata.get("length"),
                "using": metadata.get("using") or metadata.get("parameters") or [],
                "preparation_evidence": metadata.get("preparation_evidence") or [],
                "raw_metadata": metadata,
                "citation": {
                    "source_system": "cobol-rekt",
                    "chunk_id": chunk["id"],
                    "source_file": chunk["source_file"],
                    "sha256": chunk["sha256"],
                },
                "text": chunk["text"],
            }
        )
    contracts.sort(key=lambda item: (str(item.get("target") or ""), str(item.get("paragraph") or "")))
    return {
        "artifact_type": "architecture.call_contracts",
        "source_system": "combined",
        "description": "External call contracts imported from cobol-rekt knowledge-base_rag.",
        "contracts": contracts,
        "contract_count": len(contracts),
    }


def extract_chunk_family(
    artifact_type: str,
    description: str,
    chunks: list[dict[str, Any]],
    *,
    text_limit: int = 1200,
) -> dict[str, Any]:
    return {
        "artifact_type": artifact_type,
        "source_system": "combined",
        "description": description,
        "chunk_count": len(chunks),
        "chunks": [chunk_ref(chunk, text_limit=text_limit) for chunk in chunks],
    }


def find_final_dead_code_count(out_root: Path) -> int | None:
    payload = read_optional_json(artifact_path(out_root, "quality.dead_code"))
    if not isinstance(payload, dict):
        return None
    for key in ("commented_out_count", "commented_out_code_count", "commented_out_lines_count"):
        value = payload.get(key)
        if isinstance(value, int):
            return value
    content = payload.get("content") if isinstance(payload.get("content"), dict) else {}
    for key in ("commented_out_count", "commented_out_code_count", "commented_out_lines_count"):
        value = content.get(key)
        if isinstance(value, int):
            return value
    items = payload.get("commented_out_code") or payload.get("commented_out") or content.get("commented_out_code")
    if isinstance(items, list):
        return len(items)
    return None


def find_final_unused_copybooks(out_root: Path) -> dict[str, Any] | None:
    payload = read_optional_json(artifact_path(out_root, "architecture.unused_copybooks"))
    if not isinstance(payload, dict):
        return None
    content = payload.get("content") if isinstance(payload.get("content"), dict) else payload
    return {
        "copybooks": content.get("copybooks") or content.get("listed_copybooks"),
        "referenced": content.get("referenced_copybooks") or content.get("referenced"),
        "needs_review": content.get("needs_review") or content.get("possibly_unused") or content.get("unused_copybooks"),
        "raw": payload,
    }


def extract_conflicts(out_root: Path, grouped: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    conflicts = []

    final_dead_count = find_final_dead_code_count(out_root)
    rekt_commented_chunks = grouped.get("commented_out_code", [])
    rekt_inactive_counts = []
    for chunk in rekt_commented_chunks:
        metadata = chunk["metadata"]
        for key in ("inactive_line_count", "commented_out_count", "commented_out_code_count"):
            value = metadata.get(key)
            if isinstance(value, int):
                rekt_inactive_counts.append(value)
    if final_dead_count is not None and rekt_inactive_counts:
        total_rekt = sum(rekt_inactive_counts)
        if final_dead_count != total_rekt:
            conflicts.append(
                {
                    "topic": "commented_out_code",
                    "final_scripts_value": final_dead_count,
                    "cobol_rekt_value": total_rekt,
                    "policy": "prefer_final_scripts_for_commented_out_code; keep cobol-rekt as external evidence",
                    "reason": "The cobol-rekt RAG bundle reports inactive/commented-out blocks differently than the existing final_scripts quality artifact.",
                    "cobol_rekt_sources": [chunk_ref(chunk, text_limit=300) for chunk in rekt_commented_chunks],
                }
            )

    final_unused = find_final_unused_copybooks(out_root)
    rekt_unused = grouped.get("unused_copybooks", [])
    if final_unused and rekt_unused:
        final_review = final_unused.get("needs_review") or []
        rekt_candidates = []
        for chunk in rekt_unused:
            metadata = chunk["metadata"]
            candidates = metadata.get("candidate_copybooks") or metadata.get("candidates") or []
            if isinstance(candidates, list):
                rekt_candidates.extend(str(item) for item in candidates)
        if rekt_candidates and sorted(set(map(str, final_review))) != sorted(set(rekt_candidates)):
            conflicts.append(
                {
                    "topic": "unused_copybooks",
                    "final_scripts_needs_review": final_review,
                    "cobol_rekt_candidates": sorted(set(rekt_candidates)),
                    "policy": "treat both as heuristics; report union with source labels until a compiler-level usage proof exists",
                    "cobol_rekt_sources": [chunk_ref(chunk, text_limit=300) for chunk in rekt_unused],
                }
            )

    program_summaries = grouped.get("program_summary", [])
    if program_summaries:
        conflicts.append(
            {
                "topic": "line_count_methodology",
                "policy": "do not collapse different counting methods into one number",
                "note": "Existing final_scripts and cobol-rekt may count physical source lines, LOC, CFG nodes, or analyzed statements differently. Preserve labels in answers.",
                "cobol_rekt_sources": [chunk_ref(chunk, text_limit=300) for chunk in program_summaries],
            }
        )

    return {
        "artifact_type": "integration.conflicts",
        "source_system": "combined",
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
    }


def make_bundle_summary(
    *,
    bundle: Path,
    source_label: str,
    manifest: Any,
    chunks_manifest: Any,
    chunks: list[dict[str, Any]],
    grouped: dict[str, list[dict[str, Any]]],
    program: str,
) -> dict[str, Any]:
    type_counts = {key: len(value) for key, value in sorted(grouped.items())}
    selected = []
    important_types = {
        "call_contract",
        "controlflow.cfg",
        "dataflow.variable",
        "error_path",
        "paragraph_logic",
        "screen.key_dispatch",
        "screen.pagination",
        "screen.row_build",
        "screen.selection",
        "unused_copybooks",
        "dead_code",
        "commented_out_code",
        "datasets_tables_resources",
    }
    for chunk in chunks:
        if chunk["type"] in important_types:
            selected.append(chunk_ref(chunk, text_limit=250))
    return {
        "artifact_type": "integration.cobol_rekt_bundle",
        "source_system": "cobol-rekt",
        "program": program,
        "imported_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_bundle_path": source_label,
        "manifest": manifest,
        "chunks_manifest": chunks_manifest,
        "chunk_count": len(chunks),
        "chunk_type_counts": type_counts,
        "selected_chunk_refs": selected,
        "limitations": [
            "Input is the exported knowledge-base_rag bundle, not the full cobol-rekt raw report.",
            "The importer preserves cobol-rekt facts as external evidence and records conflicts instead of overwriting current final_scripts facts.",
            "Long RAG chunk text may be truncated in generated JSONL for embedding safety; original chunk hashes and source files are preserved.",
        ],
    }


def rag_record_from_chunk(chunk: dict[str, Any], *, program: str, source_label: str, max_chars: int) -> dict[str, Any]:
    metadata = chunk["metadata"]
    title_bits = [program, "cobol-rekt", chunk["type"]]
    for key in ("target", "variable", "paragraph", "title"):
        value = metadata.get(key)
        if value:
            title_bits.append(str(value))
            break
    body = str(chunk["text"] or "")
    truncated = False
    if len(body) > max_chars:
        body = body[:max_chars] + "\n[TRUNCATED_FOR_EMBEDDING_SAFETY: see original cobol-rekt chunk source_file and sha256]"
        truncated = True
    text_parts = [
        f"Program: {program}",
        "Source system: cobol-rekt knowledge-base_rag",
        f"Chunk type: {chunk['type']}",
        f"Chunk id: {chunk['id']}",
        f"Source file: {chunk['source_file']}",
    ]
    if metadata.get("paragraph"):
        text_parts.append(f"Paragraph: {metadata.get('paragraph')}")
    if metadata.get("variable"):
        text_parts.append(f"Variable: {metadata.get('variable')}")
    if metadata.get("target"):
        text_parts.append(f"Target: {metadata.get('target')}")
    text_parts.append("Content:")
    text_parts.append(body)
    rid = "cobol_rekt:" + stable_id(f"{source_label}|{chunk['source_file']}|{chunk['id']}")
    return {
        "id": rid,
        "program": program,
        "type": f"cobol_rekt.{chunk['type']}",
        "title": " ".join(title_bits),
        "text": "\n".join(text_parts),
        "metadata": {
            "source_system": "cobol-rekt",
            "source_bundle_path": source_label,
            "source_file": chunk["source_file"],
            "original_chunk_id": chunk["id"],
            "original_chunk_type": chunk["type"],
            "sha256": chunk["sha256"],
            "truncated_for_embedding": truncated,
        },
    }


def rag_record_from_artifact(path: Path, artifact_type: str, program: str, max_chars: int) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    artifact_label = display_path(path, ROOT)
    truncated = False
    if len(text) > max_chars:
        text = text[:max_chars] + "\n[TRUNCATED_FOR_EMBEDDING_SAFETY: see generated artifact file]"
        truncated = True
    rid = "combined_artifact:" + stable_id(artifact_label)
    return {
        "id": rid,
        "program": program,
        "type": artifact_type,
        "title": f"{program} {artifact_type}",
        "text": f"Program: {program}\nArtifact: {artifact_type}\nSource file: {artifact_label}\nContent:\n{text}",
        "metadata": {
            "source_system": "combined",
            "source_file": artifact_label,
            "truncated_for_embedding": truncated,
        },
    }


def write_jsonl(path: Path, records: list[dict[str, Any]], *, base_jsonl: Path | None = None) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    base_count = 0
    with path.open("w", encoding="utf-8", newline="\n") as out:
        if base_jsonl:
            with base_jsonl.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    out.write(line.rstrip("\n") + "\n")
                    base_count += 1
        for record in records:
            out.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    return {"base_count": base_count, "added_count": len(records), "total_count": base_count + len(records)}


def build_report(summary: dict[str, Any], conflicts: dict[str, Any], rag_info: dict[str, Any] | None) -> str:
    type_counts = summary["chunk_type_counts"]
    lines = [
        "# COBOL-REKT Integration Report",
        "",
        f"Program: `{summary['program']}`",
        f"Source bundle: `{summary['source_bundle_path']}`",
        f"Imported at UTC: `{summary['imported_at_utc']}`",
        "",
        "## What Was Imported",
        "",
        f"- Total cobol-rekt chunks: {summary['chunk_count']}",
    ]
    for key, count in sorted(type_counts.items()):
        lines.append(f"- {key}: {count}")
    lines.extend(
        [
            "",
            "## Added Combined Artifacts",
            "",
            "- `integration.cobol_rekt_bundle`: provenance, chunk inventory, and selected external evidence refs.",
            "- `architecture.call_contracts`: normalized external call contracts, including USING parameters and preparation evidence.",
            "- `controlflow.cfg.rich`: external control-flow chunk inventory.",
            "- `dataflow.variable.rich`: external variable/dataflow chunk inventory.",
            "- `screen.interaction`: external key dispatch, pagination, row build, and selection chunks.",
            "- `quality.error_paths.rich`: external error path chunks.",
            "- `architecture.copybook_fields`: external copybook field chunks.",
            "- `integration.conflicts`: explicit differences between current final_scripts and cobol-rekt evidence.",
            "",
            "## Conflict Policy",
            "",
            "No current final_scripts facts were overwritten. When a difference exists, the combined output preserves both facts with source labels.",
            f"Detected conflicts: {conflicts['conflict_count']}",
        ]
    )
    for conflict in conflicts.get("conflicts", []):
        lines.append(f"- {conflict.get('topic')}: {conflict.get('policy')}")
    if rag_info:
        lines.extend(
            [
                "",
                "## Combined RAG JSONL",
                "",
                f"- Base documents copied: {rag_info['base_count']}",
                f"- New cobol-rekt/combined documents added: {rag_info['added_count']}",
                f"- Total combined documents: {rag_info['total_count']}",
            ]
        )
    lines.extend(
        [
            "",
            "## How To Test",
            "",
            "Point `COBOL_RAG_FINAL_SCRIPTS_DIR` to `artifacts/combined/final_scripts` and sync the generated combined JSONL instead of replacing the stable JSONL.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program", default="PDCBVC")
    parser.add_argument("--cobol-rekt-rag-bundle", required=True)
    parser.add_argument("--source-label", help="Portable label to store in generated provenance instead of a local absolute path.")
    parser.add_argument("--final-scripts-root", default="artifacts/final/final_scripts")
    parser.add_argument("--out-root", default="artifacts/combined/final_scripts")
    parser.add_argument("--base-rag-jsonl")
    parser.add_argument("--combined-rag-jsonl", default="artifacts/combined/rag_index/control_flow_rag_documents_combined.jsonl")
    parser.add_argument("--max-rag-text-chars", type=int, default=12000)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    program = args.program.upper()
    final_scripts_root = resolve_repo_path(args.final_scripts_root, required=True)
    out_root = resolve_repo_path(args.out_root, required=True)
    bundle = resolve_bundle_path(resolve_repo_path(args.cobol_rekt_rag_bundle, required=True))
    source_label = args.source_label or f"cobol-rekt/knowledge-base_rag/{program}"
    base_rag_jsonl = resolve_repo_path(args.base_rag_jsonl) if args.base_rag_jsonl else None
    combined_rag_jsonl = resolve_repo_path(args.combined_rag_jsonl, required=True)

    manifest = read_json(bundle / "manifest.json")
    chunks_manifest_path = bundle / "chunks" / "chunks_manifest.json"
    chunks_manifest = read_json(chunks_manifest_path) if chunks_manifest_path.is_file() else {}
    chunks = load_chunks(bundle)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for chunk in chunks:
        grouped[chunk["type"]].append(chunk)

    if args.dry_run:
        print(json.dumps({"bundle": str(bundle), "chunk_count": len(chunks), "types": dict(Counter(chunk["type"] for chunk in chunks))}, indent=2))
        return 0

    copy_baseline(final_scripts_root, out_root)

    summary = make_bundle_summary(
        bundle=bundle,
        source_label=source_label,
        manifest=manifest,
        chunks_manifest=chunks_manifest,
        chunks=chunks,
        grouped=grouped,
        program=program,
    )
    write_json(artifact_path(out_root, "integration.cobol_rekt_bundle"), summary)

    write_json(
        artifact_path(out_root, "architecture.call_contracts"),
        extract_call_contracts(grouped.get("call_contract", [])),
    )
    write_json(
        artifact_path(out_root, "controlflow.cfg.rich"),
        extract_chunk_family("controlflow.cfg.rich", "Control-flow chunks imported from cobol-rekt.", grouped.get("controlflow.cfg", [])),
    )
    write_json(
        artifact_path(out_root, "dataflow.variable.rich"),
        extract_chunk_family("dataflow.variable.rich", "Variable/dataflow chunks imported from cobol-rekt.", grouped.get("dataflow.variable", [])),
    )
    screen_chunks = []
    for chunk_type in ("screen.key_dispatch", "screen.pagination", "screen.row_build", "screen.selection"):
        screen_chunks.extend(grouped.get(chunk_type, []))
    write_json(
        artifact_path(out_root, "screen.interaction"),
        extract_chunk_family("screen.interaction", "Screen interaction chunks imported from cobol-rekt.", screen_chunks),
    )
    write_json(
        artifact_path(out_root, "quality.error_paths.rich"),
        extract_chunk_family("quality.error_paths.rich", "Error path chunks imported from cobol-rekt.", grouped.get("error_path", [])),
    )
    write_json(
        artifact_path(out_root, "architecture.copybook_fields"),
        extract_chunk_family("architecture.copybook_fields", "Copybook field chunks imported from cobol-rekt.", grouped.get("copybook_fields", [])),
    )

    conflicts = extract_conflicts(out_root, grouped)
    write_json(artifact_path(out_root, "integration.conflicts"), conflicts)

    rag_records = [
        rag_record_from_chunk(chunk, program=program, source_label=source_label, max_chars=args.max_rag_text_chars)
        for chunk in chunks
    ]
    combined_artifact_files = [
        artifact_path(out_root, "integration.cobol_rekt_bundle"),
        artifact_path(out_root, "architecture.call_contracts"),
        artifact_path(out_root, "screen.interaction"),
        artifact_path(out_root, "quality.error_paths.rich"),
        artifact_path(out_root, "integration.conflicts"),
    ]
    for artifact_file in combined_artifact_files:
        rag_records.append(
            rag_record_from_artifact(
                artifact_file,
                artifact_file.parent.name,
                program,
                args.max_rag_text_chars,
            )
        )
    rag_info = write_jsonl(combined_rag_jsonl, rag_records, base_jsonl=base_rag_jsonl)
    write_json(
        combined_rag_jsonl.parent / "combined_rag_manifest.json",
        {
            "program": program,
            "source_bundle_path": source_label,
            "base_rag_jsonl": display_path(base_rag_jsonl, ROOT) if base_rag_jsonl else None,
            "combined_rag_jsonl": display_path(combined_rag_jsonl, ROOT),
            "rag_info": rag_info,
            "max_rag_text_chars": args.max_rag_text_chars,
            "chunk_type_counts": summary["chunk_type_counts"],
        },
    )

    report = build_report(summary, conflicts, rag_info)
    write_text(artifact_path(out_root, "integration.report", "integration.report.md"), report)

    print(json.dumps({"out_root": str(out_root), "combined_rag_jsonl": str(combined_rag_jsonl), "rag_info": rag_info, "conflicts": conflicts["conflict_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

