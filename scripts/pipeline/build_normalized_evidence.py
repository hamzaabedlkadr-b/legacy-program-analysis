#!/usr/bin/env python3
"""Build compact, typed evidence views without replacing analyzer artifacts.

The detailed final_scripts JSON remains the source of truth.  This file adds a
stable retrieval-facing schema whose records use the same small vocabulary for
every program: capability, entity, claim kind, facts and provenance.  It keeps
all exact statements/locations while removing analyzer-specific nesting from
the text the retriever and LLM see first.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "1.0"


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _stable_id(*parts: Any) -> str:
    raw = "\n".join(str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _fact(site: dict[str, Any], role: str, *, source_file: str = "") -> dict[str, Any]:
    return {
        "role": role,
        "paragraph": str(site.get("paragraph") or ""),
        "line_start": site.get("line_start", site.get("line", -1)),
        "line_end": site.get("line_end", site.get("line_start", site.get("line", -1))),
        "source_file": str(site.get("source_file") or source_file),
        "statement": str(site.get("statement") or ""),
    }


def _site_text(fact: dict[str, Any]) -> str:
    location = " ".join(
        value for value in (
            str(fact.get("paragraph") or ""),
            f"line {fact.get('line_start')}" if isinstance(fact.get("line_start"), int) and fact["line_start"] >= 0 else "",
        ) if value
    )
    statement = str(fact.get("statement") or "").strip()
    return f"{fact.get('role')}: {location}: {statement}".strip(": ")


def _record(
    *,
    program: str,
    capability: str,
    entity_type: str,
    entity: str,
    claim_type: str,
    summary: str,
    facts: Iterable[dict[str, Any]],
    source_artifacts: Iterable[str],
    attributes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    facts_list = list(facts)
    entity_key = f"{program}|{entity_type.upper()}|{entity.upper()}" if entity else f"{program}|PROGRAM"
    fact_preview = " ".join(_site_text(fact) for fact in facts_list[:6])
    return {
        "id": _stable_id(program, capability, entity_key, claim_type),
        "type": "evidence.normalized",
        "program": program,
        "title": f"{program} {claim_type} {entity}".strip(),
        "embedding_text": " ".join(value for value in (
            f"Program {program}.",
            f"Capability {capability}.",
            f"{entity_type} {entity}." if entity else "Program-wide evidence.",
            summary,
            fact_preview,
        ) if value),
        "content": {
            "schema_version": SCHEMA_VERSION,
            "capability": capability,
            "entity_type": entity_type,
            "entity": entity,
            "entity_key": entity_key,
            "claim_type": claim_type,
            "summary": summary,
            "facts": facts_list,
            "attributes": attributes or {},
            "provenance": {
                "source_artifacts": list(source_artifacts),
                "normalization": "lossless_view_over_final_scripts",
            },
        },
        "meta": {
            "schema_version": SCHEMA_VERSION,
            "capability": capability,
            "entity_type": entity_type,
            "entity_key": entity_key,
            "retrieval_priority": "normalized_primary",
        },
    }


def _variable_records(root: Path, program: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    canonical_path = root / "dataflow.used_variables.json"
    allowed_variables: set[str] | None = None
    if canonical_path.is_file():
        canonical = _read(canonical_path)
        variables = canonical.get("variables") if isinstance(canonical, dict) else None
        if isinstance(variables, list):
            allowed_variables = {
                str(item.get("variable") or "").strip().upper()
                for item in variables
                if isinstance(item, dict) and item.get("variable")
            }
    for path in sorted((root / "dataflow.variable").glob("*.json")):
        doc = _read(path)
        content = doc.get("content") if isinstance(doc, dict) else None
        if not isinstance(content, dict):
            continue
        variable = str(content.get("variable") or "").strip().upper()
        if not variable:
            continue
        # The aggregate artifact is the canonical inventory.  This guard also
        # prevents an old per-variable file from leaking into a reused run.
        if allowed_variables is not None and variable not in allowed_variables:
            continue
        evidence = content.get("evidence") if isinstance(content.get("evidence"), dict) else {}
        relationships = content.get("relationships") if isinstance(content.get("relationships"), dict) else {}
        facts: list[dict[str, Any]] = []
        for declaration in relationships.get("declarations") or []:
            if isinstance(declaration, dict):
                facts.append(_fact(declaration, "declaration"))
        for key, role in (
            ("write_sites", "write"),
            ("read_sites", "read"),
            ("read_write_sites", "read_write"),
            ("subscript_sites", "subscript"),
            ("control_sites", "control"),
        ):
            for site in evidence.get(key) or []:
                if isinstance(site, dict):
                    fact = _fact(site, role)
                    if fact not in facts:
                        facts.append(fact)
        summary = (
            f"Variable {variable}: origin {content.get('origin') or 'UNKNOWN'}; "
            f"{sum(f['role'] == 'declaration' for f in facts)} declaration(s), "
            f"{sum(f['role'] in {'write', 'read_write'} for f in facts)} write site(s), "
            f"{sum(f['role'] in {'read', 'read_write'} for f in facts)} read site(s), "
            f"controls flow {bool(content.get('controls_flow'))}."
        )
        records.append(_record(
            program=program,
            capability="variable_access",
            entity_type="variable",
            entity=variable,
            claim_type="variable_access",
            summary=summary,
            facts=facts,
            source_artifacts=(str(path.relative_to(root)),),
            attributes={
                "origin": content.get("origin"),
                "controls_flow": bool(content.get("controls_flow")),
                "fanout_nodes": content.get("fanout_nodes") or [],
                "parents": relationships.get("parents") or [],
                "children": relationships.get("children") or [],
                "redefines": relationships.get("redefines") or [],
                "redefined_by": relationships.get("redefined_by") or [],
            },
        ))
    return records


def _call_records(root: Path, program: str) -> list[dict[str, Any]]:
    path = root / "architecture.call_parameters.json"
    if not path.is_file():
        return []
    doc = _read(path)
    records: list[dict[str, Any]] = []
    for call in doc.get("calls") or []:
        if not isinstance(call, dict):
            continue
        target = str(call.get("target") or "").strip().upper()
        if not target:
            continue
        fact = _fact(call, "call", source_file=str(call.get("source_file") or f"{program}.CBL"))
        summary = (
            f"{program} calls {target} using {call.get('call_type') or 'CALL'}; "
            f"parameters {', '.join(str(v) for v in call.get('parameters') or []) or 'none'}; "
            f"COMMAREA {call.get('commarea') or 'none'}; LENGTH {call.get('length') or 'none'}."
        )
        records.append(_record(
            program=program,
            capability="call_evidence",
            entity_type="call",
            entity=target,
            claim_type="external_call",
            summary=summary,
            facts=(fact,),
            source_artifacts=(path.name,),
            attributes={
                "call_type": call.get("call_type"),
                "parameters": call.get("parameters") or [],
                "commarea": call.get("commarea"),
                "length": call.get("length"),
            },
        ))
    return records


def _cics_records(root: Path, program: str) -> list[dict[str, Any]]:
    path = root / "architecture.cics_operations.json"
    if not path.is_file():
        return []
    doc = _read(path)
    content = doc.get("content") if isinstance(doc.get("content"), dict) else {}
    records: list[dict[str, Any]] = []
    for operation in content.get("operations") or []:
        if not isinstance(operation, dict):
            continue
        command = str(operation.get("command") or "").strip().upper()
        if not command:
            continue
        paragraph = str(operation.get("paragraph") or "").strip().upper()
        records.append(_record(
            program=program,
            capability="cics_evidence",
            entity_type="cics_operation",
            entity=f"{command}@{paragraph or operation.get('line_start', '')}",
            claim_type="cics_operation",
            summary=f"CICS {command} is executed in {paragraph or 'an unresolved paragraph'}.",
            facts=(_fact(operation, "cics_operation"),),
            source_artifacts=(path.name,),
            attributes={
                "command": command,
                "options": operation.get("options") or [],
                "resources": operation.get("resources") or [],
            },
        ))
    return records


def _copybook_records(root: Path, program: str) -> list[dict[str, Any]]:
    path = root / "architecture.copybooks.json"
    if not path.is_file():
        return []
    doc = _read(path)
    content = doc.get("content") if isinstance(doc.get("content"), dict) else {}
    classifications: dict[str, str] = {}
    for category, values in (content.get("classified") or {}).items():
        for value in values or []:
            classifications[str(value).upper()] = str(category)
    records: list[dict[str, Any]] = []
    for inclusion in content.get("inclusions") or []:
        if not isinstance(inclusion, dict):
            continue
        copybook = str(inclusion.get("copybook") or "").strip().upper()
        if not copybook:
            continue
        records.append(_record(
            program=program,
            capability="copybook_evidence",
            entity_type="copybook",
            entity=copybook,
            claim_type="copybook_inclusion",
            summary=(
                f"COPY {copybook} is included in {inclusion.get('division') or 'unknown division'}, "
                f"{inclusion.get('section') or 'unknown section'}; classification "
                f"{classifications.get(copybook, 'unclassified')} (heuristic)."
            ),
            facts=(_fact(inclusion, "copy", source_file=str(inclusion.get("source_file") or "")),),
            source_artifacts=(path.name,),
            attributes={
                "classification": classifications.get(copybook),
                "division": inclusion.get("division"),
                "section": inclusion.get("section"),
            },
        ))
    return records


def _program_record(root: Path, program: str) -> list[dict[str, Any]]:
    path = root / "program.summary.json"
    if not path.is_file():
        return []
    doc = _read(path)
    meta = doc.get("meta") if isinstance(doc.get("meta"), dict) else {}
    summary = str(doc.get("content") or doc.get("embedding_text") or "").strip()
    return [_record(
        program=program,
        capability="program_summary",
        entity_type="program",
        entity=program,
        claim_type="program_summary",
        summary=summary,
        facts=(),
        source_artifacts=(path.name,),
        attributes={
            "loc": meta.get("loc"),
            "paragraphs": meta.get("paragraphs"),
            "statements": meta.get("statements"),
            "source": meta.get("source"),
        },
    )]


def build_normalized_evidence(root: Path, program: str) -> list[dict[str, Any]]:
    program = program.strip().upper()
    records = [
        *_program_record(root, program),
        *_variable_records(root, program),
        *_call_records(root, program),
        *_cics_records(root, program),
        *_copybook_records(root, program),
    ]
    records.sort(key=lambda item: (
        item["content"]["capability"],
        item["content"]["entity_key"],
        item["content"]["claim_type"],
    ))
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-root", required=True, type=Path)
    parser.add_argument("--program", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    records = build_normalized_evidence(args.artifacts_root, args.program)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] normalized evidence: {len(records)} records -> {args.output}")


if __name__ == "__main__":
    main()
