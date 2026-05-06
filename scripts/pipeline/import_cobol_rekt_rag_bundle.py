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


def normalize_call_type(value: Any) -> str:
    raw = str(value or "").upper()
    if "XCTL" in raw:
        return "XCTL"
    if "LINK" in raw:
        return "LINK"
    if "CALL" in raw:
        return "CALL"
    return raw


def call_entity_key(program: str, target: Any, call_type: Any) -> str:
    target_text = str(target or "").strip().upper()
    call_type_text = normalize_call_type(call_type) or "CALL"
    if not target_text:
        return ""
    return f"{program.upper()}|{target_text}|{call_type_text}"


def coverage_dimension_for_chunk_type(chunk_type: str) -> str:
    base_type = chunk_type.removeprefix("cobol_rekt.")
    if base_type in {"call_contract", "paragraph_logic", "controlflow.cfg", "workflow"}:
        return "deep_logic"
    if base_type in {"integration.conflicts"}:
        return "conflict_report"
    if base_type.startswith("quality."):
        return "quality_confidence"
    if base_type.startswith("global."):
        return "cross_program"
    return "static_inventory"


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


def artifact_candidates(root: Path, artifact_type: str) -> list[Path]:
    """Support both legacy flat artifacts and newer nested integration artifacts."""
    return [root / f"{artifact_type}.json", artifact_path(root, artifact_type)]


def read_artifact_json(root: Path, artifact_type: str) -> Any | None:
    for path in artifact_candidates(root, artifact_type):
        payload = read_optional_json(path)
        if payload is not None:
            return payload
    return None


def artifact_content(payload: Any) -> Any:
    if isinstance(payload, dict) and isinstance(payload.get("content"), (dict, list)):
        return payload["content"]
    return payload


def as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def compact_text(value: Any, limit: int = 220) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def compact_join(values: Any, *, limit: int = 8) -> str:
    items = [str(item) for item in as_list(values) if str(item).strip()]
    if not items:
        return "none recorded"
    suffix = "" if len(items) <= limit else f"; +{len(items) - limit} more"
    return ", ".join(items[:limit]) + suffix


def line_ref(site: Any) -> str:
    if not isinstance(site, dict):
        return compact_text(site)
    paragraph = site.get("paragraph") or site.get("label") or site.get("node_type") or "unknown paragraph"
    line = site.get("line_start") or site.get("line")
    statement = site.get("statement") or site.get("evidence") or ""
    prefix = f"{paragraph}"
    if isinstance(line, int) and line > 0:
        prefix += f" line {line}"
    return compact_text(f"{prefix}: {statement}")


def source_systems(*values: bool) -> list[str]:
    systems = []
    if values and values[0]:
        systems.append("mapa_hamza")
    if len(values) > 1 and values[1]:
        systems.append("cobol_rekt")
    return systems


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
    payload = read_artifact_json(out_root, "quality.dead_code")
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
    payload = read_artifact_json(out_root, "architecture.unused_copybooks")
    if not isinstance(payload, dict):
        return None
    content = payload.get("content") if isinstance(payload.get("content"), dict) else payload
    return {
        "copybooks": content.get("copybooks") or content.get("listed_copybooks"),
        "referenced": content.get("referenced_copybooks") or content.get("referenced"),
        "needs_review": (
            content.get("needs_review")
            or content.get("needs_review_copybooks")
            or content.get("possibly_unused")
            or content.get("unused_copybooks")
        ),
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
                for item in candidates:
                    if isinstance(item, dict) and item.get("copybook"):
                        rekt_candidates.append(str(item["copybook"]))
                    else:
                        rekt_candidates.append(str(item))
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
    source_chunk_type = str(chunk["type"])
    chunk_type = f"cobol_rekt.{source_chunk_type}"
    entity_metadata: dict[str, Any] = {}
    entity_key = call_entity_key(
        program,
        metadata.get("target"),
        metadata.get("command") or metadata.get("call_type") or source_chunk_type,
    )
    if entity_key:
        entity_metadata.update(
            {
                "entity_type": "call",
                "entity_key": entity_key,
                "target": str(metadata.get("target")).upper(),
                "call_type": entity_key.rsplit("|", 1)[-1],
            }
        )
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
        "type": chunk_type,
        "title": " ".join(title_bits),
        "text": "\n".join(text_parts),
        "metadata": {
            "program": program,
            "chunk_type": chunk_type,
            "source_system": "cobol_rekt",
            "source_chunk_type": source_chunk_type,
            "coverage_dimension": coverage_dimension_for_chunk_type(source_chunk_type),
            "source_bundle_path": source_label,
            "source_file": chunk["source_file"],
            "original_chunk_id": chunk["id"],
            "original_chunk_type": chunk["type"],
            "sha256": chunk["sha256"],
            "truncated_for_embedding": truncated,
            **entity_metadata,
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
            "program": program,
            "chunk_type": artifact_type,
            "source_system": "integration",
            "source_chunk_type": artifact_type,
            "coverage_dimension": coverage_dimension_for_chunk_type(artifact_type),
            "source_file": artifact_label,
            "truncated_for_embedding": truncated,
        },
    }


def call_entities_from_jsonl(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.is_file():
        return {}
    entities: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
            entity_key = str(metadata.get("entity_key") or "")
            if not entity_key or metadata.get("entity_type") != "call":
                continue
            source_system = str(metadata.get("source_system") or "mapa_hamza")
            if source_system not in {"mapa_hamza", "mapa", "hamza"}:
                continue
            entities.setdefault(
                entity_key,
                {
                    "entity_key": entity_key,
                    "source_system": "mapa_hamza",
                    "chunk_type": metadata.get("chunk_type") or record.get("type"),
                    "record_id": record.get("id"),
                    "title": record.get("title"),
                },
            )
    return entities


def call_entities_from_records(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    entities: dict[str, dict[str, Any]] = {}
    for record in records:
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        entity_key = str(metadata.get("entity_key") or "")
        if not entity_key or metadata.get("entity_type") != "call":
            continue
        entities.setdefault(
            entity_key,
            {
                "entity_key": entity_key,
                "source_system": metadata.get("source_system"),
                "chunk_type": metadata.get("chunk_type") or record.get("type"),
                "record_id": record.get("id"),
                "title": record.get("title"),
            },
        )
    return entities


def load_mapa_call_facts(final_scripts_root: Path, program: str) -> dict[str, dict[str, Any]]:
    payload = read_artifact_json(final_scripts_root, "architecture.call_parameters")
    content = artifact_content(payload)
    facts: dict[str, dict[str, Any]] = {}
    for call in as_list(content.get("calls") if isinstance(content, dict) else None):
        if not isinstance(call, dict):
            continue
        entity_key = call_entity_key(program, call.get("target"), call.get("call_type"))
        if not entity_key:
            continue
        facts[entity_key] = {
            "entity_key": entity_key,
            "target": call.get("target"),
            "call_type": normalize_call_type(call.get("call_type")),
            "paragraph": call.get("paragraph"),
            "line_start": call.get("line_start"),
            "statement": call.get("statement"),
            "parameters": call.get("parameters") or [],
            "commarea": call.get("commarea"),
            "length": call.get("length"),
            "parameter_details": call.get("parameter_details") or [],
            "source_file": "architecture.call_parameters.json",
        }
    return facts


def load_mapa_variable_facts(final_scripts_root: Path) -> dict[str, dict[str, Any]]:
    facts: dict[str, dict[str, Any]] = {}
    for path in sorted((final_scripts_root / "dataflow.variable").glob("dataflow.variable.*.json")):
        payload = read_optional_json(path)
        content = artifact_content(payload)
        if not isinstance(content, dict):
            continue
        variable = str(content.get("variable") or "").upper()
        if not variable:
            continue
        facts[variable] = {
            "variable": variable,
            "defined_in": content.get("defined_in") or [],
            "modified_in": content.get("modified_in") or [],
            "used_in": content.get("used_in") or [],
            "controls_flow": bool(content.get("controls_flow")),
            "fanout_nodes": content.get("fanout_nodes") or [],
            "origin": content.get("origin"),
            "evidence": content.get("evidence") if isinstance(content.get("evidence"), dict) else {},
            "source_file": display_path(path, ROOT),
        }
    return facts


def load_mapa_paragraph_facts(final_scripts_root: Path) -> dict[str, dict[str, Any]]:
    payload = read_artifact_json(final_scripts_root, "controlflow.cfg")
    content = artifact_content(payload)
    facts: dict[str, dict[str, Any]] = {}
    if not isinstance(content, dict):
        return facts
    for node in as_list(content.get("nodes")):
        name = str(node or "").upper()
        if name:
            facts.setdefault(name, {"paragraph": name, "incoming": [], "outgoing": []})
    for edge in as_list(content.get("edges")):
        if not isinstance(edge, dict):
            continue
        source = str(edge.get("from") or "").upper()
        target = str(edge.get("to") or "").upper()
        summary = {
            "from": source,
            "to": target,
            "type": edge.get("type"),
            "condition": edge.get("condition"),
            "evidence": edge.get("evidence"),
            "cics_ops": edge.get("cics_ops") or [],
        }
        if source:
            facts.setdefault(source, {"paragraph": source, "incoming": [], "outgoing": []})["outgoing"].append(summary)
        if target:
            facts.setdefault(target, {"paragraph": target, "incoming": [], "outgoing": []})["incoming"].append(summary)
    return facts


def group_rekt_by_key(chunks: list[dict[str, Any]], metadata_key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for chunk in chunks:
        value = chunk["metadata"].get(metadata_key)
        if value:
            grouped[str(value).upper()].append(chunk)
    return grouped


def rekt_calls_by_entity(chunks: list[dict[str, Any]], program: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for chunk in chunks:
        metadata = chunk["metadata"]
        entity_key = call_entity_key(program, metadata.get("target"), metadata.get("command") or metadata.get("call_type"))
        if entity_key:
            grouped[entity_key].append(chunk)
    return grouped


def source_balance_artifact(program: str) -> dict[str, Any]:
    return {
        "artifact_type": "integration.source_balance",
        "source_system": "integration",
        "program": program,
        "purpose": "Guide combined answers to use each evidence source for its strongest facts instead of producing canned prose.",
        "policy": [
            {
                "question_area": "call inventory, copybooks, exact lines, control-flow edges, variable read/write sites",
                "primary_source": "mapa_hamza",
                "use_cobol_rekt_for": "nearby preparation context, call contracts, paragraph summaries, workflow and error-path detail",
            },
            {
                "question_area": "what a paragraph or workflow does",
                "primary_source": "cobol_rekt",
                "use_mapa_hamza_for": "graph position, callers/callees, exact line evidence and variable facts",
            },
            {
                "question_area": "variable lifecycle",
                "primary_source": "mapa_hamza",
                "use_cobol_rekt_for": "expanded read/write site context and data-group/origin clues",
            },
            {
                "question_area": "conflicting counts or heuristic quality findings",
                "primary_source": "integration.conflicts",
                "use_cobol_rekt_for": "external evidence only; do not overwrite MAPA/final_scripts facts",
            },
        ],
        "answer_style": [
            "Synthesize from retrieved facts; do not return this policy as an answer.",
            "Name source labels only when they clarify confidence or a difference.",
            "Prefer concrete code facts over broad business interpretations.",
            "If one source is silent, answer from the other source and say what was not found.",
        ],
    }


def make_source_balance_record(program: str) -> dict[str, Any]:
    text = (
        f"Program: {program}\n"
        "Type: integration.source_balance\n"
        "Use MAPA/Hamza as the primary source for exact static inventory: calls, copybooks, control-flow edges, "
        "line references, and variable read/write/control sites. Use cobol-rekt as the primary source for "
        "paragraph-level intent, call-contract preparation context, workflow summaries, screen behavior, and "
        "error-path detail. When both describe the same entity, combine the exact MAPA fact with the richer "
        "cobol-rekt context. When facts disagree, preserve both with source labels and consult integration.conflicts."
    )
    return {
        "id": "integration_source_balance:" + stable_id(program),
        "program": program,
        "type": "integration.source_balance",
        "title": f"{program} source balance guide",
        "text": text,
        "metadata": {
            "program": program,
            "chunk_type": "integration.source_balance",
            "source_system": "integration",
            "source_chunk_type": "integration.source_balance",
            "coverage_dimension": "cross_program",
        },
    }


def make_call_context_records(
    *,
    program: str,
    final_scripts_root: Path,
    chunks: list[dict[str, Any]],
    source_label: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    mapa_facts = load_mapa_call_facts(final_scripts_root, program)
    rekt_facts = rekt_calls_by_entity(
        [chunk for chunk in chunks if chunk["type"] == "call_contract"],
        program,
    )
    records: list[dict[str, Any]] = []
    artifact_contexts: list[dict[str, Any]] = []
    for entity_key in sorted(set(mapa_facts) | set(rekt_facts)):
        _program, target, call_type = entity_key.split("|", 2)
        mapa = mapa_facts.get(entity_key)
        rekt_chunks = rekt_facts.get(entity_key, [])
        lines = [
            f"Program: {program}",
            "Type: integration.call_context",
            f"Call entity: {target} via {call_type}",
            "Source balance: MAPA/Hamza is used for exact call inventory and line-level call facts; cobol-rekt is used for preparation, contract, workflow, and error-path context.",
        ]
        if mapa:
            lines.append(
                "MAPA/Hamza call fact: "
                f"{target} is invoked from {mapa.get('paragraph') or 'unknown paragraph'}"
                f"{' line ' + str(mapa.get('line_start')) if mapa.get('line_start') else ''}"
                f" with parameters {compact_join(mapa.get('parameters'))}."
            )
            if mapa.get("statement"):
                lines.append(f"MAPA/Hamza statement: {compact_text(mapa.get('statement'), 500)}")
            details = []
            for detail in as_list(mapa.get("parameter_details"))[:6]:
                if not isinstance(detail, dict):
                    continue
                variables = [
                    item.get("variable")
                    for item in as_list(detail.get("variables"))
                    if isinstance(item, dict) and item.get("variable")
                ]
                details.append(f"{detail.get('parameter')}: {compact_join(variables, limit=10)}")
            if details:
                lines.append("MAPA/Hamza parameter variables: " + " | ".join(details))
        else:
            lines.append("MAPA/Hamza call fact: no matching static call record was found for this call key.")

        if rekt_chunks:
            contract_chunks = [chunk for chunk in rekt_chunks if chunk["type"] == "call_contract"]
            if contract_chunks:
                evidence = []
                for item in as_list(contract_chunks[0]["metadata"].get("preparation_evidence"))[:8]:
                    evidence.append(compact_text(item, 260))
                lines.append("cobol-rekt call-contract context: " + ((" | ".join(evidence)) if evidence else compact_text(contract_chunks[0]["text"], 900)))
            other_refs = [
                f"{chunk['type']}:{chunk['metadata'].get('paragraph') or chunk['metadata'].get('target') or chunk['id']}"
                for chunk in rekt_chunks
                if chunk["type"] != "call_contract"
            ]
            if other_refs:
                lines.append("cobol-rekt related context chunks: " + compact_join(other_refs, limit=10))
        else:
            lines.append("cobol-rekt context: no matching call-contract chunk was found for this call key.")

        rid = "integration_call_context:" + stable_id(entity_key)
        metadata = {
            "program": program,
            "chunk_type": "integration.call_context",
            "source_system": "integration",
            "source_chunk_type": "integration.call_context",
            "coverage_dimension": "cross_program",
            "entity_type": "call",
            "entity_key": entity_key,
            "target": target,
            "call_type": call_type,
            "source_systems": source_systems(bool(mapa), bool(rekt_chunks)),
            "mapa_record": mapa,
            "cobol_rekt_refs": [chunk_ref(chunk, text_limit=300) for chunk in rekt_chunks[:12]],
            "source_bundle_path": source_label,
        }
        records.append(
            {
                "id": rid,
                "program": program,
                "type": "integration.call_context",
                "title": f"{program} combined call context {target}",
                "text": "\n".join(lines),
                "metadata": metadata,
            }
        )
        artifact_contexts.append(metadata)
    return records, {
        "artifact_type": "integration.call_contexts",
        "source_system": "integration",
        "program": program,
        "context_count": len(records),
        "contexts": artifact_contexts,
    }


def make_paragraph_context_records(
    *,
    program: str,
    final_scripts_root: Path,
    chunks: list[dict[str, Any]],
    source_label: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    mapa_facts = load_mapa_paragraph_facts(final_scripts_root)
    rekt_by_paragraph = group_rekt_by_key(
        [chunk for chunk in chunks if chunk["type"] in {"paragraph_logic", "controlflow.cfg", "workflow", "screen.row_build", "screen.selection", "screen.key_dispatch", "screen.pagination", "error_path"}],
        "paragraph",
    )
    for chunk in chunks:
        if chunk["type"] == "workflow" and chunk["metadata"].get("entry_paragraph"):
            rekt_by_paragraph[str(chunk["metadata"]["entry_paragraph"]).upper()].append(chunk)
    records: list[dict[str, Any]] = []
    artifact_contexts: list[dict[str, Any]] = []
    for paragraph in sorted(set(mapa_facts) | set(rekt_by_paragraph)):
        rekt_chunks = rekt_by_paragraph.get(paragraph, [])
        if not rekt_chunks and paragraph not in mapa_facts:
            continue
        mapa = mapa_facts.get(paragraph)
        lines = [
            f"Program: {program}",
            "Type: integration.paragraph_context",
            f"Paragraph: {paragraph}",
            "Source balance: cobol-rekt is used for paragraph intent and workflow detail; MAPA/Hamza is used for exact graph edges and code evidence.",
        ]
        if mapa:
            outgoing = mapa.get("outgoing") or []
            incoming = mapa.get("incoming") or []
            lines.append(f"MAPA/Hamza graph fact: {len(incoming)} incoming edge(s), {len(outgoing)} outgoing edge(s).")
            for edge in outgoing[:6]:
                condition = f" when {edge.get('condition')}" if edge.get("condition") else ""
                lines.append(f"MAPA/Hamza outgoing: {edge.get('type')} to {edge.get('to')}{condition}; evidence: {compact_text(edge.get('evidence'), 260)}")
        else:
            lines.append("MAPA/Hamza graph fact: no exact control-flow node was found for this paragraph.")
        if rekt_chunks:
            seen_summary_keys: set[tuple[str, str]] = set()
            for chunk in rekt_chunks[:8]:
                metadata = chunk["metadata"]
                summary_key = (chunk["type"], str(metadata.get("source_id") or metadata.get("chunk_id") or chunk["id"]))
                if summary_key in seen_summary_keys:
                    continue
                seen_summary_keys.add(summary_key)
                if chunk["type"] == "paragraph_logic":
                    lines.append(
                        "cobol-rekt paragraph logic: "
                        f"{metadata.get('comment_english') or compact_text(chunk['text'], 260)}; "
                        f"reads {compact_join(metadata.get('variables_read'), limit=8)}; "
                        f"modifies {compact_join(metadata.get('variables_modified'), limit=8)}."
                    )
                elif chunk["type"] == "workflow":
                    lines.append(
                        "cobol-rekt workflow: "
                        f"orchestrates {compact_join(metadata.get('called_paragraphs'), limit=8)}."
                    )
                else:
                    lines.append(f"cobol-rekt {chunk['type']}: {compact_text(chunk['text'], 360)}")
        else:
            lines.append("cobol-rekt context: no paragraph-level chunk was found.")
        rid = "integration_paragraph_context:" + stable_id(f"{program}|{paragraph}")
        metadata = {
            "program": program,
            "chunk_type": "integration.paragraph_context",
            "source_system": "integration",
            "source_chunk_type": "integration.paragraph_context",
            "coverage_dimension": "deep_logic",
            "entity_type": "paragraph",
            "paragraph": paragraph,
            "source_systems": source_systems(bool(mapa), bool(rekt_chunks)),
            "mapa_record": mapa,
            "cobol_rekt_refs": [chunk_ref(chunk, text_limit=300) for chunk in rekt_chunks[:12]],
            "source_bundle_path": source_label,
        }
        records.append(
            {
                "id": rid,
                "program": program,
                "type": "integration.paragraph_context",
                "title": f"{program} combined paragraph context {paragraph}",
                "text": "\n".join(lines),
                "metadata": metadata,
            }
        )
        artifact_contexts.append(metadata)
    return records, {
        "artifact_type": "integration.paragraph_contexts",
        "source_system": "integration",
        "program": program,
        "context_count": len(records),
        "contexts": artifact_contexts,
    }


def make_variable_context_records(
    *,
    program: str,
    final_scripts_root: Path,
    chunks: list[dict[str, Any]],
    source_label: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    mapa_facts = load_mapa_variable_facts(final_scripts_root)
    rekt_by_variable = group_rekt_by_key(
        [chunk for chunk in chunks if chunk["type"] in {"dataflow.variable", "variable_group", "static_values"}],
        "variable",
    )
    records: list[dict[str, Any]] = []
    artifact_contexts: list[dict[str, Any]] = []
    for variable in sorted(set(mapa_facts) | set(rekt_by_variable)):
        mapa = mapa_facts.get(variable)
        rekt_chunks = rekt_by_variable.get(variable, [])
        if not mapa and not rekt_chunks:
            continue
        lines = [
            f"Program: {program}",
            "Type: integration.variable_context",
            f"Variable: {variable}",
            "Source balance: MAPA/Hamza is used for concise lifecycle and exact read/write/control sites; cobol-rekt is used for expanded dataflow context and origin grouping.",
        ]
        if mapa:
            evidence = mapa.get("evidence") or {}
            lines.append(
                "MAPA/Hamza variable fact: "
                f"defined in {compact_join(mapa.get('defined_in'))}; modified in {compact_join(mapa.get('modified_in'))}; "
                f"used in {compact_join(mapa.get('used_in'))}; controls flow: {'yes' if mapa.get('controls_flow') else 'no'}."
            )
            for label, key in (("write", "write_sites"), ("read", "read_sites"), ("control", "control_sites")):
                sites = as_list(evidence.get(key))
                if sites:
                    lines.append(f"MAPA/Hamza {label} evidence: " + " | ".join(line_ref(site) for site in sites[:5]))
        else:
            lines.append("MAPA/Hamza variable fact: no generated variable artifact was found.")
        if rekt_chunks:
            metadata = rekt_chunks[0]["metadata"]
            origin = metadata.get("origin_group") or metadata.get("group") or metadata.get("source_id")
            lines.append(
                "cobol-rekt variable context: "
                f"origin/group {origin or 'not recorded'}; "
                f"reads {metadata.get('read_count', 'not counted')}; writes {metadata.get('write_count', 'not counted')}."
            )
            for chunk in rekt_chunks[:4]:
                lines.append(f"cobol-rekt {chunk['type']}: {compact_text(chunk['text'], 360)}")
        else:
            lines.append("cobol-rekt context: no variable chunk was found.")
        rid = "integration_variable_context:" + stable_id(f"{program}|{variable}")
        metadata = {
            "program": program,
            "chunk_type": "integration.variable_context",
            "source_system": "integration",
            "source_chunk_type": "integration.variable_context",
            "coverage_dimension": "cross_program",
            "entity_type": "variable",
            "variable": variable,
            "source_systems": source_systems(bool(mapa), bool(rekt_chunks)),
            "mapa_record": mapa,
            "cobol_rekt_refs": [chunk_ref(chunk, text_limit=300) for chunk in rekt_chunks[:10]],
            "source_bundle_path": source_label,
        }
        records.append(
            {
                "id": rid,
                "program": program,
                "type": "integration.variable_context",
                "title": f"{program} combined variable context {variable}",
                "text": "\n".join(lines),
                "metadata": metadata,
            }
        )
        artifact_contexts.append(metadata)
    return records, {
        "artifact_type": "integration.variable_contexts",
        "source_system": "integration",
        "program": program,
        "context_count": len(records),
        "contexts": artifact_contexts,
    }


def make_entity_link_records(
    *,
    program: str,
    base_rag_jsonl: Path | None,
    cobol_rekt_records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    mapa_entities = call_entities_from_jsonl(base_rag_jsonl)
    rekt_entities = call_entities_from_records(cobol_rekt_records)
    records: list[dict[str, Any]] = []
    for entity_key in sorted(set(mapa_entities) & set(rekt_entities)):
        _program, target, call_type = entity_key.split("|", 2)
        rid = "integration_entity_link:" + stable_id(entity_key)
        text = (
            f"Program: {program}\n"
            "Type: integration.entity_link\n"
            f"Entity: call {target} via {call_type}\n"
            "MAPA/Hamza provides static call inventory evidence. "
            "cobol-rekt provides deep call-contract evidence for the same call entity."
        )
        records.append(
            {
                "id": rid,
                "program": program,
                "type": "integration.entity_link",
                "title": f"{program} linked call {target}",
                "text": text,
                "metadata": {
                    "program": program,
                    "chunk_type": "integration.entity_link",
                    "source_system": "integration",
                    "source_chunk_type": "integration.entity_link",
                    "coverage_dimension": "cross_program",
                    "entity_type": "call",
                    "entity_key": entity_key,
                    "target": target,
                    "call_type": call_type,
                    "left_source_system": "mapa_hamza",
                    "right_source_system": "cobol_rekt",
                },
            }
        )
    artifact = {
        "artifact_type": "integration.entity_links",
        "source_system": "integration",
        "entity_type": "call",
        "link_count": len(records),
        "links": [record["metadata"] for record in records],
    }
    return records, artifact


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
            "- `integration.source_balance`: guidance for using MAPA/Hamza and cobol-rekt according to each source's strongest evidence.",
            "- `integration.call_contexts`, `integration.paragraph_contexts`, and `integration.variable_contexts`: neutral synthesis records that link exact MAPA/Hamza facts with cobol-rekt context without prewriting answers.",
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
    source_balance = source_balance_artifact(program)
    write_json(artifact_path(out_root, "integration.source_balance"), source_balance)

    call_context_records, call_contexts_artifact = make_call_context_records(
        program=program,
        final_scripts_root=final_scripts_root,
        chunks=chunks,
        source_label=source_label,
    )
    write_json(artifact_path(out_root, "integration.call_contexts"), call_contexts_artifact)
    paragraph_context_records, paragraph_contexts_artifact = make_paragraph_context_records(
        program=program,
        final_scripts_root=final_scripts_root,
        chunks=chunks,
        source_label=source_label,
    )
    write_json(artifact_path(out_root, "integration.paragraph_contexts"), paragraph_contexts_artifact)
    variable_context_records, variable_contexts_artifact = make_variable_context_records(
        program=program,
        final_scripts_root=final_scripts_root,
        chunks=chunks,
        source_label=source_label,
    )
    write_json(artifact_path(out_root, "integration.variable_contexts"), variable_contexts_artifact)

    rag_records = [
        rag_record_from_chunk(chunk, program=program, source_label=source_label, max_chars=args.max_rag_text_chars)
        for chunk in chunks
    ]
    rag_records.append(make_source_balance_record(program))
    rag_records.extend(call_context_records)
    rag_records.extend(paragraph_context_records)
    rag_records.extend(variable_context_records)
    combined_artifact_files = [
        artifact_path(out_root, "integration.cobol_rekt_bundle"),
        artifact_path(out_root, "integration.source_balance"),
        artifact_path(out_root, "integration.call_contexts"),
        artifact_path(out_root, "integration.paragraph_contexts"),
        artifact_path(out_root, "integration.variable_contexts"),
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
    entity_link_records, entity_links_artifact = make_entity_link_records(
        program=program,
        base_rag_jsonl=base_rag_jsonl,
        cobol_rekt_records=rag_records,
    )
    if entity_link_records:
        write_json(artifact_path(out_root, "integration.entity_links"), entity_links_artifact)
        rag_records.extend(entity_link_records)
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
            "integration_context_counts": {
                "call_contexts": len(call_context_records),
                "paragraph_contexts": len(paragraph_context_records),
                "variable_contexts": len(variable_context_records),
                "entity_links": len(entity_link_records),
            },
        },
    )

    report = build_report(summary, conflicts, rag_info)
    write_text(artifact_path(out_root, "integration.report", "integration.report.md"), report)

    print(json.dumps({"out_root": str(out_root), "combined_rag_jsonl": str(combined_rag_jsonl), "rag_info": rag_info, "conflicts": conflicts["conflict_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
