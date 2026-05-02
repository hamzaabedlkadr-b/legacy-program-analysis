#!/usr/bin/env python3
"""Build cross-program RAG maps from per-program artifact outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


GLOBAL_PROGRAM = "__GLOBAL__"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build global cross-program RAG map documents.")
    parser.add_argument(
        "--out-root",
        required=True,
        type=Path,
        help="Pipeline output root. Can be the folder containing programs/ or programs/ itself.",
    )
    parser.add_argument("--package-root", type=Path, help="Optional per-program package root.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        help="Destination folder for global map docs. Default: <out-root>/_global/rag_maps.",
    )
    parser.add_argument(
        "--min-shared-programs",
        type=int,
        default=2,
        help="Minimum program count for shared variable docs.",
    )
    parser.add_argument(
        "--min-structure-vars",
        type=int,
        default=3,
        help="Minimum variables with the same prefix for common-structure docs.",
    )
    parser.add_argument(
        "--max-control-variable-docs",
        type=int,
        default=3000,
        help="Maximum control-variable docs to emit in addition to shared variables.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def stable_id(*parts: Any) -> str:
    raw = "\n".join(str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", (text or "").strip()).strip("_") or "ITEM"


def unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        item = (item or "").strip().upper()
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def resolve_programs_dir(out_root: Path) -> Path:
    if (out_root / "programs").is_dir():
        return out_root / "programs"
    if out_root.is_dir() and any((child / "artifacts").is_dir() for child in out_root.iterdir() if child.is_dir()):
        return out_root
    raise SystemExit(f"Could not find programs output folder under: {out_root}")


def iter_program_dirs(programs_dir: Path) -> list[Path]:
    return sorted(child for child in programs_dir.iterdir() if child.is_dir())


def doc(doc_type: str, title: str, embedding_text: str, content: dict[str, Any], meta: dict[str, Any] | None = None, evidence: list[str] | None = None) -> dict[str, Any]:
    return {
        "id": stable_id(doc_type, title, json.dumps(content, sort_keys=True, ensure_ascii=False)),
        "type": doc_type,
        "program": GLOBAL_PROGRAM,
        "title": title,
        "embedding_text": embedding_text,
        "content": content,
        "meta": meta or {"source": "global_rag_maps"},
        "evidence": evidence or [],
    }


def read_program_artifacts(program_dir: Path) -> dict[str, Any]:
    artifacts = program_dir / "artifacts"
    data: dict[str, Any] = {
        "program": program_dir.name.upper(),
        "copybooks": None,
        "calls": [],
        "db2_tables": [],
        "variables": [],
    }

    copybooks_path = artifacts / "architecture.copybooks.json"
    if copybooks_path.is_file():
        try:
            data["copybooks"] = load_json(copybooks_path)
        except Exception:
            data["copybooks"] = None

    call_dir = artifacts / "architecture.call"
    if call_dir.is_dir():
        for path in sorted(call_dir.glob("*.json")):
            try:
                data["calls"].append(load_json(path))
            except Exception:
                continue
    elif (artifacts / "architecture.calls.json").is_file():
        try:
            summary = load_json(artifacts / "architecture.calls.json")
            for call_type, item in (summary.get("content") or {}).items():
                for target in item.get("targets") or []:
                    data["calls"].append(
                        {
                            "type": "architecture.call",
                            "program": data["program"],
                            "content": {
                                "caller": data["program"],
                                "call_type": call_type,
                                "target": target,
                                "heuristic_intent": item.get("heuristic_intent"),
                                "intent_confidence": item.get("intent_confidence"),
                            },
                            "evidence": summary.get("evidence") or [],
                        }
                    )
        except Exception:
            pass

    db2_dir = artifacts / "architecture.db2_table"
    if db2_dir.is_dir():
        for path in sorted(db2_dir.glob("*.json")):
            try:
                data["db2_tables"].append(load_json(path))
            except Exception:
                continue

    used_vars = artifacts / "dataflow.used_variables.json"
    if used_vars.is_file():
        try:
            payload = load_json(used_vars)
            variables = payload.get("variables") if isinstance(payload, dict) else None
            if isinstance(variables, list):
                data["variables"] = [v for v in variables if isinstance(v, dict)]
        except Exception:
            pass

    return data


def iter_package_manifests(package_root: Path | None) -> dict[str, dict[str, Any]]:
    if not package_root or not package_root.is_dir():
        return {}
    manifests: dict[str, dict[str, Any]] = {}
    for path in sorted(package_root.glob("*/manifest.json")):
        try:
            payload = load_json(path)
        except Exception:
            continue
        program = str(payload.get("program") or path.parent.name).upper()
        manifests[program] = payload
    return manifests


def copybook_stem(path_text: str) -> str:
    return Path(path_text).stem.upper()


def build_copybook_docs(program_data: list[dict[str, Any]], manifests: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    usage: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "programs": set(),
            "categories": set(),
            "present_in_packages": set(),
            "missing_in_packages": set(),
            "evidence": [],
        }
    )

    for item in program_data:
        program = item["program"]
        payload = item.get("copybooks") or {}
        content = payload.get("content") or {}
        for copybook in unique(list(content.get("all") or [])):
            entry = usage[copybook]
            entry["programs"].add(program)
        for category, names in (content.get("classified") or {}).items():
            for copybook in unique(list(names or [])):
                entry = usage[copybook]
                entry["programs"].add(program)
                entry["categories"].add(category)
        for evidence in payload.get("evidence") or []:
            parts = str(evidence).split(",")
            if len(parts) >= 4 and parts[0].upper() == "COPY":
                usage[parts[-1].strip().upper()]["evidence"].append(evidence)

    for program, manifest in manifests.items():
        files = (manifest.get("files") or {}).get("copybooks") or []
        for file_text in files:
            usage[copybook_stem(file_text)]["present_in_packages"].add(program)
        missing = (manifest.get("missing") or {}).get("copybooks") or []
        for copybook in unique(list(missing)):
            usage[copybook]["missing_in_packages"].add(program)
            usage[copybook]["programs"].add(program)

    docs: list[dict[str, Any]] = []
    index_rows: list[dict[str, Any]] = []
    for copybook in sorted(usage):
        entry = usage[copybook]
        programs = sorted(entry["programs"])
        categories = sorted(entry["categories"])
        missing = sorted(entry["missing_in_packages"])
        present = sorted(entry["present_in_packages"])
        row = {
            "copybook": copybook,
            "program_count": len(programs),
            "programs": programs,
            "categories": categories,
            "present_in_packages": present,
            "missing_in_packages": missing,
        }
        index_rows.append(row)
        docs.append(
            doc(
                "global.copybook_usage",
                f"Copybook {copybook} usage",
                (
                    f"Copybook {copybook} is used by {len(programs)} program(s): {', '.join(programs[:25])}. "
                    f"Categories: {', '.join(categories) if categories else 'unclassified'}. "
                    f"Missing from packages for: {', '.join(missing) if missing else 'none'}."
                ),
                row,
                meta={"source": "global_rag_maps", "entity": "copybook", "copybook": copybook},
                evidence=list(entry["evidence"])[:30],
            )
        )

    summary = {
        "copybook_count": len(index_rows),
        "program_count": len({program for row in index_rows for program in row["programs"]}),
        "top_copybooks": sorted(index_rows, key=lambda row: (-row["program_count"], row["copybook"]))[:50],
        "missing_copybooks": [row for row in index_rows if row["missing_in_packages"]],
    }
    docs.insert(
        0,
        doc(
            "global.copybook_usage.summary",
            "Global copybook usage summary",
            f"Global copybook usage map across {summary['program_count']} program(s) and {summary['copybook_count']} copybook(s).",
            summary,
            meta={"source": "global_rag_maps", "entity": "copybook_summary"},
        ),
    )
    return docs, summary


def build_call_docs(program_data: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    program_names = {item["program"] for item in program_data}
    edges: list[dict[str, Any]] = []
    by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_caller: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_type: Counter[str] = Counter()

    for item in program_data:
        program = item["program"]
        for call in item.get("calls") or []:
            content = call.get("content") or {}
            target = str(content.get("target") or "").upper()
            call_type = str(content.get("call_type") or "UNKNOWN").upper()
            if not target:
                continue
            edge = {
                "caller": str(content.get("caller") or program).upper(),
                "target": target,
                "call_type": call_type,
                "heuristic_intent": content.get("heuristic_intent"),
                "intent_confidence": content.get("intent_confidence"),
                "target_is_in_program_set": target in program_names,
            }
            edges.append(edge)
            by_target[target].append(edge)
            by_caller[edge["caller"]].append(edge)
            by_type[call_type] += 1

    docs: list[dict[str, Any]] = []
    for target in sorted(by_target):
        incoming = sorted(by_target[target], key=lambda e: (e["caller"], e["call_type"]))
        callers = sorted({edge["caller"] for edge in incoming})
        call_types = sorted({edge["call_type"] for edge in incoming})
        content = {
            "target": target,
            "caller_count": len(callers),
            "callers": callers,
            "call_types": call_types,
            "incoming_edges": incoming,
            "target_is_in_program_set": target in program_names,
        }
        docs.append(
            doc(
                "global.call_target",
                f"Call target {target}",
                f"Call target {target} is called by {len(callers)} program(s): {', '.join(callers[:30])}. Call types: {', '.join(call_types)}.",
                content,
                meta={"source": "global_rag_maps", "entity": "call_target", "target": target},
            )
        )

    for caller in sorted(by_caller):
        outgoing = sorted(by_caller[caller], key=lambda e: (e["target"], e["call_type"]))
        targets = sorted({edge["target"] for edge in outgoing})
        content = {
            "caller": caller,
            "target_count": len(targets),
            "targets": targets,
            "outgoing_edges": outgoing,
        }
        docs.append(
            doc(
                "global.program_dependencies",
                f"Program {caller} dependencies",
                f"Program {caller} calls {len(targets)} target(s): {', '.join(targets[:30])}.",
                content,
                meta={"source": "global_rag_maps", "entity": "program_dependencies", "program": caller},
            )
        )

    summary = {
        "edge_count": len(edges),
        "caller_count": len(by_caller),
        "target_count": len(by_target),
        "call_type_counts": dict(sorted(by_type.items())),
        "external_targets": sorted(target for target in by_target if target not in program_names),
        "top_targets": sorted(
            [
                {"target": target, "caller_count": len({edge["caller"] for edge in incoming}), "edge_count": len(incoming)}
                for target, incoming in by_target.items()
            ],
            key=lambda row: (-row["caller_count"], -row["edge_count"], row["target"]),
        )[:50],
    }
    docs.insert(
        0,
        doc(
            "global.call_graph.summary",
            "Global call graph summary",
            f"Global call graph has {summary['edge_count']} edge(s), {summary['caller_count']} caller(s), and {summary['target_count']} target(s).",
            summary,
            meta={"source": "global_rag_maps", "entity": "call_graph_summary"},
        ),
    )
    return docs, summary


def build_db2_docs(program_data: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_table: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_stmt: Counter[str] = Counter()
    for item in program_data:
        program = item["program"]
        for table_doc in item.get("db2_tables") or []:
            content = table_doc.get("content") or {}
            table = str(content.get("table") or "").upper()
            stmt_type = str(content.get("stmt_type") or "unknown")
            if not table:
                continue
            usage = {
                "program": program,
                "table": table,
                "stmt_type": stmt_type,
                "evidence": table_doc.get("evidence") or [],
            }
            by_table[table].append(usage)
            by_stmt[stmt_type] += 1

    docs: list[dict[str, Any]] = []
    for table in sorted(by_table):
        usages = sorted(by_table[table], key=lambda row: (row["program"], row["stmt_type"]))
        programs = sorted({row["program"] for row in usages})
        stmt_types = sorted({row["stmt_type"] for row in usages})
        content = {
            "table": table,
            "program_count": len(programs),
            "programs": programs,
            "statement_types": stmt_types,
            "usages": usages,
        }
        docs.append(
            doc(
                "global.db2_table_usage",
                f"DB2 table {table} usage",
                f"DB2 table {table} is used by {len(programs)} program(s): {', '.join(programs[:30])}. Statement types: {', '.join(stmt_types)}.",
                content,
                meta={"source": "global_rag_maps", "entity": "db2_table", "table": table},
                evidence=[ev for row in usages for ev in row.get("evidence", [])][:30],
            )
        )

    summary = {
        "table_count": len(by_table),
        "usage_count": sum(len(rows) for rows in by_table.values()),
        "statement_type_counts": dict(sorted(by_stmt.items())),
        "top_tables": sorted(
            [{"table": table, "program_count": len({row["program"] for row in rows}), "usage_count": len(rows)} for table, rows in by_table.items()],
            key=lambda row: (-row["program_count"], -row["usage_count"], row["table"]),
        )[:50],
    }
    docs.insert(
        0,
        doc(
            "global.db2_table_usage.summary",
            "Global DB2 table usage summary",
            f"Global DB2 map covers {summary['table_count']} table(s) and {summary['usage_count']} usage record(s).",
            summary,
            meta={"source": "global_rag_maps", "entity": "db2_table_summary"},
        ),
    )
    return docs, summary


def scan_jcl_artifacts(out_root: Path, manifests: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    jobs: dict[str, dict[str, Any]] = {}
    program_to_jobs: dict[str, set[str]] = defaultdict(set)

    jcl_root = out_root / "_global" / "jcl"
    if jcl_root.is_dir():
        for summary_path in sorted(jcl_root.glob("*/jcl.summary.json")):
            try:
                summary = load_json(summary_path)
            except Exception:
                continue
            job = str(summary.get("job") or summary_path.parent.name).upper()
            programs = unique(list(summary.get("programs") or []))
            jobs[job] = {
                "job": job,
                "source": summary.get("source"),
                "purpose": summary.get("purpose"),
                "programs": programs,
                "procedures": summary.get("procedures") or [],
                "steps_count": summary.get("steps_count"),
                "datasets_count": summary.get("datasets_count"),
                "warnings": summary.get("warnings") or [],
                "artifact_dir": str(summary_path.parent),
            }
            for program in programs:
                program_to_jobs[program].add(job)

    for package_program, manifest in manifests.items():
        jcl_files = (manifest.get("files") or {}).get("jcl") or []
        for jcl_file in jcl_files:
            job = Path(jcl_file).stem.upper()
            jobs.setdefault(
                job,
                {
                    "job": job,
                    "source": jcl_file,
                    "purpose": None,
                    "programs": [],
                    "procedures": [],
                    "steps_count": None,
                    "datasets_count": None,
                    "warnings": [],
                    "artifact_dir": None,
                },
            )
            if package_program not in jobs[job]["programs"]:
                jobs[job]["programs"].append(package_program)
            program_to_jobs[package_program].add(job)

    docs: list[dict[str, Any]] = []
    for job in sorted(jobs):
        item = jobs[job]
        programs = unique(list(item.get("programs") or []))
        item["programs"] = programs
        docs.append(
            doc(
                "global.jcl_job",
                f"JCL job {job}",
                f"JCL job {job} references {len(programs)} program(s): {', '.join(programs[:30])}.",
                item,
                meta={"source": "global_rag_maps", "entity": "jcl_job", "job": job},
            )
        )
    for program in sorted(program_to_jobs):
        job_list = sorted(program_to_jobs[program])
        content = {"program": program, "jobs": job_list, "job_count": len(job_list)}
        docs.append(
            doc(
                "global.jcl_program_map",
                f"JCL jobs for program {program}",
                f"Program {program} is referenced by {len(job_list)} JCL job(s): {', '.join(job_list[:30])}.",
                content,
                meta={"source": "global_rag_maps", "entity": "jcl_program", "program": program},
            )
        )

    summary = {
        "job_count": len(jobs),
        "program_count": len(program_to_jobs),
        "jobs": [jobs[job] for job in sorted(jobs)],
        "program_to_jobs": {program: sorted(job_set) for program, job_set in sorted(program_to_jobs.items())},
    }
    docs.insert(
        0,
        doc(
            "global.jcl_program_map.summary",
            "Global JCL to program map summary",
            f"Global JCL map covers {summary['job_count']} job(s) and {summary['program_count']} program(s).",
            summary,
            meta={"source": "global_rag_maps", "entity": "jcl_program_summary"},
        ),
    )
    return docs, summary


def variable_prefix(name: str) -> str:
    value = (name or "").upper().strip()
    if "-" not in value:
        return value
    return value.split("-", 1)[0]


def build_variable_docs(program_data: list[dict[str, Any]], min_shared_programs: int, min_structure_vars: int, max_control_docs: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    variables: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "programs": set(),
            "origins": set(),
            "defined_in": defaultdict(set),
            "modified_in": defaultdict(set),
            "used_in": defaultdict(set),
            "controls_flow_programs": set(),
            "fanout_nodes": defaultdict(set),
        }
    )
    structures: dict[str, dict[str, Any]] = defaultdict(lambda: {"variables": set(), "programs": set(), "origins": set(), "control_variables": set()})

    for item in program_data:
        program = item["program"]
        for var in item.get("variables") or []:
            name = str(var.get("variable") or "").upper()
            if not name:
                continue
            entry = variables[name]
            entry["programs"].add(program)
            origin = str(var.get("origin") or "UNKNOWN").upper()
            entry["origins"].add(origin)
            for paragraph in var.get("defined_in") or []:
                entry["defined_in"][program].add(str(paragraph))
            for paragraph in var.get("modified_in") or []:
                entry["modified_in"][program].add(str(paragraph))
            for paragraph in var.get("used_in") or []:
                entry["used_in"][program].add(str(paragraph))
            if var.get("controls_flow"):
                entry["controls_flow_programs"].add(program)
            for node in var.get("fanout_nodes") or []:
                entry["fanout_nodes"][program].add(str(node))

            prefix = variable_prefix(name)
            if prefix and len(prefix) > 1:
                structures[prefix]["variables"].add(name)
                structures[prefix]["programs"].add(program)
                structures[prefix]["origins"].add(origin)
                if var.get("controls_flow"):
                    structures[prefix]["control_variables"].add(name)

    docs: list[dict[str, Any]] = []
    variable_rows: list[dict[str, Any]] = []
    control_candidates: list[tuple[str, dict[str, Any]]] = []
    for name, entry in variables.items():
        programs = sorted(entry["programs"])
        controls_flow_programs = sorted(entry["controls_flow_programs"])
        row = {
            "variable": name,
            "program_count": len(programs),
            "programs": programs,
            "origins": sorted(entry["origins"]),
            "controls_flow_programs": controls_flow_programs,
            "defined_in": {program: sorted(values) for program, values in sorted(entry["defined_in"].items())},
            "modified_in": {program: sorted(values) for program, values in sorted(entry["modified_in"].items())},
            "used_in": {program: sorted(values) for program, values in sorted(entry["used_in"].items())},
            "fanout_nodes": {program: sorted(values) for program, values in sorted(entry["fanout_nodes"].items())},
        }
        variable_rows.append(row)
        if len(programs) >= min_shared_programs:
            docs.append(
                doc(
                    "global.shared_variable",
                    f"Shared variable {name}",
                    f"Variable {name} appears in {len(programs)} program(s): {', '.join(programs[:30])}. Origins: {', '.join(row['origins'])}.",
                    row,
                    meta={"source": "global_rag_maps", "entity": "shared_variable", "variable": name},
                )
            )
        elif controls_flow_programs:
            control_candidates.append((name, row))

    control_candidates.sort(key=lambda item: (-len(item[1]["controls_flow_programs"]), item[0]))
    for name, row in control_candidates[:max_control_docs]:
        docs.append(
            doc(
                "global.control_variable_usage",
                f"Control variable {name}",
                f"Variable {name} controls flow in {len(row['controls_flow_programs'])} program(s): {', '.join(row['controls_flow_programs'][:30])}.",
                row,
                meta={"source": "global_rag_maps", "entity": "control_variable", "variable": name},
            )
        )

    structure_rows: list[dict[str, Any]] = []
    for prefix, entry in structures.items():
        programs = sorted(entry["programs"])
        variables_list = sorted(entry["variables"])
        if len(programs) < min_shared_programs and len(variables_list) < min_structure_vars:
            continue
        row = {
            "structure": prefix,
            "program_count": len(programs),
            "programs": programs,
            "variable_count": len(variables_list),
            "sample_variables": variables_list[:100],
            "origins": sorted(entry["origins"]),
            "control_variables": sorted(entry["control_variables"]),
        }
        structure_rows.append(row)
        docs.append(
            doc(
                "global.common_structure",
                f"Common structure/prefix {prefix}",
                f"Structure/prefix {prefix} appears in {len(programs)} program(s) with {len(variables_list)} variable(s).",
                row,
                meta={"source": "global_rag_maps", "entity": "common_structure", "structure": prefix},
            )
        )

    summary = {
        "variable_count": len(variable_rows),
        "shared_variable_count": sum(1 for row in variable_rows if row["program_count"] >= min_shared_programs),
        "control_variable_count": len(control_candidates),
        "common_structure_count": len(structure_rows),
        "top_shared_variables": sorted(variable_rows, key=lambda row: (-row["program_count"], row["variable"]))[:50],
        "top_common_structures": sorted(structure_rows, key=lambda row: (-row["program_count"], -row["variable_count"], row["structure"]))[:50],
    }
    docs.insert(
        0,
        doc(
            "global.shared_variables.summary",
            "Global shared variables and common structures summary",
            (
                f"Global variable map covers {summary['variable_count']} variable(s), "
                f"{summary['shared_variable_count']} shared variable(s), and {summary['common_structure_count']} common structure prefix(es)."
            ),
            summary,
            meta={"source": "global_rag_maps", "entity": "shared_variables_summary"},
        ),
    )
    return docs, summary


def write_docs(out_dir: Path, docs_by_section: dict[str, list[dict[str, Any]]], manifest: dict[str, Any]) -> None:
    for section, docs in docs_by_section.items():
        section_dir = out_dir / section
        section_dir.mkdir(parents=True, exist_ok=True)
        for item in docs:
            title_key = item.get("meta", {}).get("copybook") or item.get("meta", {}).get("target") or item.get("meta", {}).get("table") or item.get("meta", {}).get("job") or item.get("meta", {}).get("program") or item.get("meta", {}).get("variable") or item.get("meta", {}).get("structure") or item["type"]
            filename = f"{safe_name(item['type'])}.{safe_name(str(title_key))}.json"
            save_json(section_dir / filename, item)
        save_json(out_dir / f"{section}.rag_documents.json", docs)

    all_docs = [item for docs in docs_by_section.values() for item in docs]
    save_json(out_dir / "global.rag_documents.json", all_docs)
    save_json(out_dir / "global_maps_manifest.json", manifest)

    lines = [
        "# Global RAG Maps",
        "",
        f"- Programs: {manifest['program_count']}",
        f"- Global docs: {manifest['global_document_count']}",
        "",
        "| Section | Documents | Summary |",
        "|---|---:|---|",
    ]
    for section, info in manifest["sections"].items():
        lines.append(f"| {section} | {info['document_count']} | {info['summary']} |")
    (out_dir / "global_maps_manifest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_global_maps(args: argparse.Namespace) -> dict[str, Any]:
    programs_dir = resolve_programs_dir(args.out_root)
    out_dir = args.out_dir or (programs_dir.parent / "_global" / "rag_maps")
    manifests = iter_package_manifests(args.package_root)
    program_data = [read_program_artifacts(program_dir) for program_dir in iter_program_dirs(programs_dir)]

    copybook_docs, copybook_summary = build_copybook_docs(program_data, manifests)
    call_docs, call_summary = build_call_docs(program_data)
    db2_docs, db2_summary = build_db2_docs(program_data)
    jcl_docs, jcl_summary = scan_jcl_artifacts(programs_dir.parent, manifests)
    variable_docs, variable_summary = build_variable_docs(
        program_data,
        min_shared_programs=max(1, args.min_shared_programs),
        min_structure_vars=max(1, args.min_structure_vars),
        max_control_docs=max(0, args.max_control_variable_docs),
    )

    docs_by_section = {
        "copybook_usage": copybook_docs,
        "call_graph": call_docs,
        "db2_table_usage": db2_docs,
        "jcl_program_map": jcl_docs,
        "shared_variables": variable_docs,
    }
    manifest = {
        "out_root": str(args.out_root),
        "programs_dir": str(programs_dir),
        "package_root": str(args.package_root) if args.package_root else None,
        "out_dir": str(out_dir),
        "program_count": len(program_data),
        "global_document_count": sum(len(docs) for docs in docs_by_section.values()),
        "sections": {
            "copybook_usage": {
                "document_count": len(copybook_docs),
                "summary": f"{copybook_summary['copybook_count']} copybooks",
                "details": copybook_summary,
            },
            "call_graph": {
                "document_count": len(call_docs),
                "summary": f"{call_summary['edge_count']} call edges",
                "details": call_summary,
            },
            "db2_table_usage": {
                "document_count": len(db2_docs),
                "summary": f"{db2_summary['table_count']} DB2 tables",
                "details": db2_summary,
            },
            "jcl_program_map": {
                "document_count": len(jcl_docs),
                "summary": f"{jcl_summary['job_count']} JCL jobs",
                "details": jcl_summary,
            },
            "shared_variables": {
                "document_count": len(variable_docs),
                "summary": f"{variable_summary['shared_variable_count']} shared variables, {variable_summary['common_structure_count']} structures",
                "details": variable_summary,
            },
        },
    }
    write_docs(out_dir, docs_by_section, manifest)
    return manifest


def main() -> int:
    args = parse_args()
    manifest = build_global_maps(args)
    print(f"[OK] Wrote {manifest['global_document_count']} global RAG map docs")
    print(f"[OK] Output: {manifest['out_dir']}")
    print(f"[OK] Manifest: {Path(manifest['out_dir']) / 'global_maps_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
