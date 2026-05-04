#!/usr/bin/env python3
"""Build derived review artifacts from generated COBOL analysis JSON.

This script makes the "review" artifacts first-class analysis outputs instead
of relying on the downstream RAG app to synthesize them at query time.
It supports both artifact layouts used in this repository:

* final_scripts layout:
  final_scripts/program.comments/program.comments.json
* pipeline layout:
  output/programs/PROG/artifacts/program.comments.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DERIVED_TYPES = (
    "quality.dead_code",
    "architecture.unused_copybooks",
    "jcl.file_io",
    "screen_field_lineage",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate derived dead-code, COPY review, file-I/O, and screen lineage artifacts."
    )
    parser.add_argument(
        "--root",
        required=True,
        type=Path,
        help="Program artifact root or final_scripts root.",
    )
    parser.add_argument("--program", required=True, help="COBOL program name, e.g. PDCBVC.")
    parser.add_argument(
        "--layout",
        choices=("auto", "pipeline", "final-scripts"),
        default="auto",
        help="Output layout. auto detects from the supplied root.",
    )
    parser.add_argument(
        "--jcl-root",
        type=Path,
        help="Optional parsed JCL artifact root. Defaults to <root>/jcl.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print a summary without writing files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    program = args.program.upper()
    layout = detect_layout(root) if args.layout == "auto" else args.layout
    jcl_root = args.jcl_root.resolve() if args.jcl_root else root / "jcl"

    artifacts = build_all(root, program, jcl_root)
    if args.dry_run:
        print_summary(root, layout, artifacts)
        return 0

    written = write_artifacts(root, program, layout, artifacts)
    print_summary(root, layout, artifacts)
    for path in written:
        print(f"[OK] wrote {path}")
    return 0


def detect_layout(root: Path) -> str:
    if (root / "program.comments.json").is_file() or (root / "controlflow.cfg.json").is_file():
        return "pipeline"
    return "final-scripts"


def build_all(root: Path, program: str, jcl_root: Path) -> dict[str, dict[str, Any]]:
    return {
        "quality.dead_code": build_quality_dead_code(root, program),
        "architecture.unused_copybooks": build_unused_copybooks(root, program),
        "jcl.file_io": build_jcl_file_io(root, program, jcl_root),
        "screen_field_lineage": build_screen_field_lineage(root, program),
    }


def write_artifacts(
    root: Path,
    program: str,
    layout: str,
    artifacts: dict[str, dict[str, Any]],
) -> list[Path]:
    if layout == "pipeline":
        targets = {
            "quality.dead_code": root / "quality.dead_code.json",
            "architecture.unused_copybooks": root / "architecture.unused_copybooks.json",
            "jcl.file_io": root / "jcl.file_io.json",
            "screen_field_lineage": root / "screen_field_lineage.json",
        }
    else:
        targets = {
            "quality.dead_code": root / "quality.dead_code" / "quality.dead_code.json",
            "architecture.unused_copybooks": root / "architecture.unused_copybooks" / "architecture.unused_copybooks.json",
            "jcl.file_io": root / "jcl.file_io" / f"jcl.file_io.{program}.json",
            "screen_field_lineage": root / "screen_field_lineage" / "screen_field_lineage.json",
        }

    written: list[Path] = []
    for artifact_type in DERIVED_TYPES:
        target = targets[artifact_type]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(artifacts[artifact_type], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(target)
    return written


def print_summary(root: Path, layout: str, artifacts: dict[str, dict[str, Any]]) -> None:
    dead = artifacts["quality.dead_code"]["content"]
    unused = artifacts["architecture.unused_copybooks"]["content"]
    file_io = artifacts["jcl.file_io"]["content"]
    screen = artifacts["screen_field_lineage"]["content"]
    print(f"[INFO] root={root}")
    print(f"[INFO] layout={layout}")
    print(
        "[INFO] quality.dead_code "
        f"commented_out={dead['commented_out_code_count']} "
        f"unreachable={dead['cfg_reachability']['unreachable_nodes_count']}"
    )
    print(
        "[INFO] architecture.unused_copybooks "
        f"copybooks={unused['copybooks_total']} "
        f"referenced={len(unused['referenced_copybooks'])} "
        f"needs_review={unused['needs_review_count']}"
    )
    print(
        "[INFO] jcl.file_io "
        f"jobs={file_io['matching_jobs_count']} "
        f"steps={file_io['matching_steps_count']} "
        f"reads={len(file_io['reads'])} writes={len(file_io['writes'])}"
    )
    print(
        "[INFO] screen_field_lineage "
        f"fields={screen['fields_count']} "
        f"copybooks={', '.join(screen['copybook_origins']) or 'none'}"
    )


def build_quality_dead_code(root: Path, program: str) -> dict[str, Any]:
    comments = read_artifact(root, "program.comments")
    cfg = read_artifact(root, "controlflow.cfg")
    comments_source = artifact_source(root, "program.comments")
    commented_out: list[dict[str, Any]] = []

    if artifact_program(comments) == program:
        for comment in comments.get("comments", []):
            if not isinstance(comment, dict) or comment.get("classification") != "commented_out_code":
                continue
            commented_out.append(
                {
                    "line": comment.get("line"),
                    "section": comment.get("section"),
                    "paragraph": comment.get("paragraph"),
                    "kind": comment.get("kind"),
                    "text": str(comment.get("text_raw") or comment.get("text") or "").strip(),
                    "classification_reason": comment.get("classification_reason"),
                    "citation": citation(comments_source, line=comment.get("line")),
                }
            )

    reachability = cfg_reachability(cfg, program)
    return {
        "schema_version": 1,
        "type": "quality.dead_code",
        "program": program,
        "title": f"{program} dead-code and commented-code evidence",
        "content": {
            "commented_out_code_count": len(commented_out),
            "commented_out_code": commented_out,
            "cfg_reachability": reachability,
            "unreachable_paragraphs": reachability.get("unreachable_nodes", []),
            "limitations": [
                "commented_out_code is direct evidence from program.comments.",
                "cfg_reachability is static and limited to nodes present in controlflow.cfg.",
                "An empty unreachable_paragraphs list is not a runtime proof that every statement executes.",
            ],
        },
        "evidence": {
            "comments_artifact": artifact_source(root, "program.comments"),
            "cfg_artifact": artifact_source(root, "controlflow.cfg"),
        },
    }


def build_unused_copybooks(root: Path, program: str) -> dict[str, Any]:
    payload = read_artifact(root, "architecture.copybooks")
    if artifact_program(payload) == program:
        content = payload.get("content", {})
        all_copybooks = [str(item).upper() for item in content.get("all", [])]
        classified = {
            str(name): [str(item).upper() for item in values]
            for name, values in content.get("classified", {}).items()
            if isinstance(values, list)
        }
    else:
        all_copybooks = []
        classified = {}

    evidence = copybook_evidence(root, program, all_copybooks)
    referenced = sorted(name for name, items in evidence.items() if items)
    needs_review = [name for name in all_copybooks if name not in referenced]
    statuses = [
        {
            "copybook": name,
            "status": "referenced_by_available_artifacts"
            if evidence.get(name)
            else "needs_review_no_reference_in_available_artifacts",
            "evidence": evidence.get(name, []),
        }
        for name in all_copybooks
    ]

    return {
        "schema_version": 1,
        "type": "architecture.unused_copybooks",
        "program": program,
        "title": f"{program} COPY usage review",
        "content": {
            "copybooks_total": len(all_copybooks),
            "all_copybooks": all_copybooks,
            "classified": classified,
            "referenced_copybooks": referenced,
            "needs_review_count": len(needs_review),
            "needs_review_copybooks": needs_review,
            "unused_copybooks_proven": [],
            "copybook_status": statuses,
            "proof_level": "available-artifact-reference review; not compiler-expanded source proof",
            "limitations": [
                "This artifact does not prove COPY members are unused.",
                "needs_review_copybooks are members with no reference evidence in the available artifacts.",
                "A compiler-expanded source or copybook field-level parser is needed for stronger proof.",
            ],
        },
        "evidence": {
            "copybooks_artifact": artifact_source(root, "architecture.copybooks"),
            "dataflow_artifacts": [
                artifact_source(root, "dataflow.used_variables"),
                "dataflow.variable/*.json",
                artifact_source(root, "dataflow.literal_assignments"),
                artifact_source(root, "architecture.call_parameters"),
            ],
        },
    }


def build_jcl_file_io(root: Path, program: str, jcl_root: Path) -> dict[str, Any]:
    summaries = jcl_summaries(jcl_root)
    steps = jcl_steps(jcl_root)
    matching_jobs = []
    matching_steps = []
    reads: list[dict[str, Any]] = []
    writes: list[dict[str, Any]] = []
    sysout: list[dict[str, Any]] = []

    for summary in summaries:
        programs = {str(item).upper() for item in summary.get("programs", [])}
        if program in programs:
            matching_jobs.append(summary_item(summary))

    for step in steps:
        step_program = str(step.get("program") or step.get("target") or "").upper()
        if step_program != program:
            continue
        matching_steps.append(step_item(step))
        reads.extend(dd_items(step, {"read"}))
        writes.extend(dd_items(step, {"write", "delete"}))
        sysout.extend(dd_items(step, {"sysout"}))

    matching_jobs = unique_dicts(matching_jobs, ("job",))
    matching_steps = unique_dicts(matching_steps, ("job", "step", "program"))
    reads = unique_dicts(reads, ("job", "step", "ddname", "dsn", "access_type"))
    writes = unique_dicts(writes, ("job", "step", "ddname", "dsn", "access_type"))
    sysout = unique_dicts(sysout, ("job", "step", "ddname", "sysout", "output", "access_type"))
    known_jobs = sorted({str(summary.get("job", "")) for summary in summaries if summary.get("job")})
    known_programs = sorted(
        {
            str(item).upper()
            for summary in summaries
            for item in summary.get("programs", [])
            if str(item).strip()
        }
    )

    return {
        "schema_version": 1,
        "type": "jcl.file_io",
        "program": program,
        "title": f"{program} JCL file I/O evidence",
        "content": {
            "matching_jobs_count": len(matching_jobs),
            "matching_jobs": matching_jobs,
            "matching_steps_count": len(matching_steps),
            "matching_steps": matching_steps,
            "reads": reads,
            "writes": writes,
            "sysout": sysout,
            "has_jcl_linkage": bool(matching_jobs or matching_steps),
            "known_jobs": known_jobs,
            "known_programs_sample": known_programs[:30],
            "limitations": [
                "This artifact maps file I/O through JCL step summaries only.",
                "CICS online programs often have no JCL dataset production evidence.",
                "Program-to-JCL linkage depends on parsed EXEC PGM/procedure summaries.",
            ],
        },
        "evidence": {
            "jcl_root": str(jcl_root),
        },
    }


def build_screen_field_lineage(root: Path, program: str) -> dict[str, Any]:
    variables = screen_variable_payloads(root, program)
    by_name = {str(payload.get("content", {}).get("variable", "")).upper(): payload for payload in variables}
    literals_by_target = literal_assignments_by_target(root, program)
    fields: list[dict[str, Any]] = []

    for name, payload in sorted(by_name.items()):
        content = payload.get("content", {})
        family = screen_family(name)
        family_members = sorted(candidate for candidate in by_name if screen_family(candidate) == family)
        literal_assignments = []
        for member in family_members:
            literal_assignments.extend(literals_by_target.get(member, []))
        fields.append(
            {
                "field": name,
                "family": family,
                "family_members": family_members,
                "origin": content.get("origin"),
                "defined_in": content.get("defined_in", []),
                "modified_in": content.get("modified_in", []),
                "used_in": content.get("used_in", []),
                "controls_flow": bool(content.get("controls_flow")),
                "fanout_nodes": content.get("fanout_nodes", []),
                "write_sites": site_items(name, content, "write_sites"),
                "read_sites": site_items(name, content, "read_sites"),
                "control_sites": site_items(name, content, "control_sites"),
                "literal_assignments": literal_assignments,
                "related_variables": related_variables_for_screen_field(name, payload, by_name.keys()),
                "source_artifact": f"dataflow.variable/dataflow.variable.{name}.json",
            }
        )

    copybook_origins = sorted(
        {
            str(field.get("origin", "")).split(":", 1)[1]
            for field in fields
            if str(field.get("origin", "")).startswith("COPY:")
        }
    )
    return {
        "schema_version": 1,
        "type": "screen_field_lineage",
        "program": program,
        "title": f"{program} screen/map field lineage",
        "content": {
            "fields_count": len(fields),
            "fields": fields,
            "copybook_origins": copybook_origins,
            "limitations": [
                "Lineage is derived from dataflow.variable artifacts and literal assignments.",
                "Input-origin values entered by terminal users have read/control evidence but may not have write evidence in COBOL.",
                "Family grouping uses common BMS suffixes such as I, O, L, A, and F.",
            ],
        },
        "evidence": {
            "variable_artifacts": "dataflow.variable/dataflow.variable.*.json",
            "literal_artifact": artifact_source(root, "dataflow.literal_assignments"),
        },
    }


def cfg_reachability(cfg: Any, program: str) -> dict[str, Any]:
    if not isinstance(cfg, dict) or artifact_program(cfg) != program:
        return {
            "status": "not_available",
            "entry": program,
            "nodes_count": 0,
            "reachable_nodes_count": 0,
            "unreachable_nodes_count": 0,
            "unreachable_nodes": [],
        }

    edges = [edge for edge in cfg.get("edges", []) if isinstance(edge, dict)]
    nodes = {program}
    adjacency: dict[str, set[str]] = {}
    for edge in edges:
        source = str(edge.get("from", "")).upper()
        target = str(edge.get("to", "")).upper()
        if not source or not target:
            continue
        nodes.add(source)
        nodes.add(target)
        adjacency.setdefault(source, set()).add(target)

    seen = {program}
    stack = [program]
    while stack:
        node = stack.pop()
        for target in adjacency.get(node, set()):
            if target in seen:
                continue
            seen.add(target)
            stack.append(target)

    unreachable = sorted(nodes - seen)
    return {
        "status": "computed_from_controlflow_cfg",
        "entry": program,
        "nodes_count": len(nodes),
        "reachable_nodes_count": len(seen),
        "unreachable_nodes_count": len(unreachable),
        "unreachable_nodes": unreachable,
    }


def copybook_evidence(root: Path, program: str, known_copybooks: list[str]) -> dict[str, list[dict[str, Any]]]:
    evidence: dict[str, list[dict[str, Any]]] = {name: [] for name in known_copybooks}

    def mark(copybook: str, source: str, detail: str, line: Any | None = None) -> None:
        copybook = copybook.upper()
        if copybook not in evidence:
            return
        item = {"source": source, "detail": detail}
        if line not in (None, "", -1):
            item["line"] = line
        item["citation"] = citation(source, line=line, detail=detail)
        if item not in evidence[copybook]:
            evidence[copybook].append(item)

    def mark_by_value(value: Any, source: str, detail: str, line: Any | None = None) -> None:
        text = str(value).upper()
        if not text:
            return
        if text.startswith("COPY:"):
            mark(text.split(":", 1)[1], source, detail, line=line)
        for copybook in known_copybooks:
            if text == copybook or text.startswith(f"{copybook}-"):
                mark(copybook, source, detail, line=line)

    used = read_artifact(root, "dataflow.used_variables")
    used_source = artifact_source(root, "dataflow.used_variables")
    if artifact_program(used) == program:
        for variable in used.get("variables", []):
            if not isinstance(variable, dict):
                continue
            name = str(variable.get("variable", ""))
            origin = str(variable.get("origin", ""))
            line = first_site_line(variable)
            mark_by_value(name, used_source, f"variable {name}", line=line)
            mark_by_value(origin, used_source, f"origin {origin}", line=line)
            if origin == "CICS_CONST" and (name.startswith("DFHPF") or name == "DFHENTER"):
                mark("DFHAID", used_source, f"CICS AID constant {name}", line=line)

    for path in iter_artifact_files(root, "dataflow.variable"):
        payload = read_json(path)
        if not isinstance(payload, dict) or artifact_program(payload) != program:
            continue
        source = relative_path(root, path)
        content = payload.get("content", {})
        variable = str(content.get("variable", ""))
        origin = str(content.get("origin", ""))
        line = first_site_line(content)
        mark_by_value(variable, source, f"variable {variable}", line=line)
        mark_by_value(origin, source, f"origin {origin}", line=line)

    literals = read_artifact(root, "dataflow.literal_assignments")
    literals_source = artifact_source(root, "dataflow.literal_assignments")
    if artifact_program(literals) == program:
        for item in literals.get("assignments", []):
            if isinstance(item, dict):
                target = str(item.get("target_variable", ""))
                mark_by_value(target, literals_source, f"literal assignment target {target}", item.get("line"))

    calls = read_artifact(root, "architecture.call_parameters")
    calls_source = artifact_source(root, "architecture.call_parameters")
    if artifact_program(calls) == program:
        for call in calls.get("calls", []):
            if not isinstance(call, dict):
                continue
            line = call.get("line_start")
            for parameter in call.get("parameters", []):
                mark_by_value(parameter, calls_source, f"call parameter {parameter}", line)
            for detail in call.get("parameter_details", []):
                if not isinstance(detail, dict):
                    continue
                mark_by_value(detail.get("field_prefix", ""), calls_source, "parameter field prefix", line)
                for variable in detail.get("variables", []):
                    if isinstance(variable, dict):
                        var_line = first_call_parameter_line(variable) or line
                        mark_by_value(
                            variable.get("variable", ""),
                            calls_source,
                            "parameter variable",
                            var_line,
                        )

    return evidence


def screen_variable_payloads(root: Path, program: str) -> list[dict[str, Any]]:
    variables = []
    screen_copybooks = screen_copybook_names(root, program)
    for path in iter_artifact_files(root, "dataflow.variable"):
        payload = read_json(path)
        if not isinstance(payload, dict) or artifact_program(payload) != program:
            continue
        origin = str(payload.get("content", {}).get("origin", "")).upper()
        if origin.startswith("COPY:") and origin.split(":", 1)[1] in screen_copybooks:
            variables.append(payload)
    return variables


def screen_copybook_names(root: Path, program: str) -> set[str]:
    result: set[str] = set()
    nav = read_artifact(root, "ui.cics.navigation")
    if artifact_program(nav) == program:
        for item in nav.get("content", {}).get("maps", []):
            mapset = str(item.get("mapset", "")).upper()
            if mapset:
                result.add(mapset)
    if not result:
        copybooks = read_artifact(root, "architecture.copybooks")
        if artifact_program(copybooks) == program:
            for name in copybooks.get("content", {}).get("classified", {}).get("ui_cics", []):
                text = str(name).upper()
                if text.endswith("M"):
                    result.add(text)
    return result


def literal_assignments_by_target(root: Path, program: str) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    payload = read_artifact(root, "dataflow.literal_assignments")
    if artifact_program(payload) != program:
        return result
    for item in payload.get("assignments", []):
        if not isinstance(item, dict) or not item.get("screen_or_map_field"):
            continue
        target = str(item.get("target_variable", "")).upper()
        result.setdefault(target, []).append(
            {
                "target_variable": target,
                "literal": item.get("literal"),
                "paragraph": item.get("paragraph"),
                "line": item.get("line"),
                "statement": item.get("statement"),
                "citation": citation("dataflow.literal_assignments", line=item.get("line"), detail=target),
            }
        )
    return result


def site_items(variable: str, content: dict[str, Any], key: str) -> list[dict[str, Any]]:
    sites = []
    for site in content.get("evidence", {}).get(key, []):
        if not isinstance(site, dict):
            continue
        line = site.get("line_start")
        sites.append(
            {
                "paragraph": site.get("paragraph"),
                "line_start": line,
                "statement": site.get("statement"),
                "citation": citation(f"dataflow.variable.{variable}", line=line),
            }
        )
    return sites


def related_variables_for_screen_field(
    variable: str,
    payload: dict[str, Any],
    screen_names: Any,
) -> list[dict[str, Any]]:
    names = {str(name).upper() for name in screen_names}
    related: dict[str, dict[str, Any]] = {}
    content = payload.get("content", {})
    for key in ("write_sites", "read_sites", "control_sites"):
        for site in content.get("evidence", {}).get(key, []):
            statement = str(site.get("statement", ""))
            for token in tokens_from_statement(statement):
                if token == variable.upper() or token in names or is_cobol_keyword(token):
                    continue
                item = {
                    "variable": token,
                    "paragraph": site.get("paragraph"),
                    "line": site.get("line_start"),
                    "statement": statement,
                    "relationship": f"appears with {variable.upper()} in {key}",
                    "citation": citation(f"dataflow.variable.{variable.upper()}", line=site.get("line_start"), detail=token),
                }
                existing = related.get(token)
                if existing and positive_line(existing.get("line")) and not positive_line(item.get("line")):
                    continue
                related[token] = item
    return sorted(related.values(), key=lambda item: (str(item.get("variable")), int(item.get("line") or 0)))


def jcl_summaries(jcl_root: Path) -> list[dict[str, Any]]:
    summaries = []
    for path in sorted(jcl_root.glob("**/jcl.summary.json")):
        payload = read_json(path)
        if isinstance(payload, dict):
            payload["__artifact_path"] = relative_path(jcl_root, path)
            summaries.append(payload)
    return summaries


def jcl_steps(jcl_root: Path) -> list[dict[str, Any]]:
    steps = []
    for path in sorted(jcl_root.glob("**/jcl.steps.*.json")):
        payload = read_json(path)
        if isinstance(payload, dict):
            payload["__artifact_path"] = relative_path(jcl_root, path)
            steps.append(payload)
    return steps


def summary_item(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "job": summary.get("job"),
        "purpose": summary.get("purpose"),
        "source": summary.get("source"),
        "source_artifact": summary.get("__artifact_path"),
        "programs": summary.get("programs", []),
        "steps_count": summary.get("steps_count"),
        "datasets_count": summary.get("datasets_count"),
        "external_inputs_count": summary.get("external_inputs_count"),
    }


def step_item(step: dict[str, Any]) -> dict[str, Any]:
    return {
        "job": step.get("job"),
        "step": step.get("step"),
        "program": step.get("program") or step.get("target"),
        "scope": step.get("scope"),
        "source": step.get("source"),
        "source_artifact": step.get("__artifact_path"),
        "reads_count": len(step.get("reads", [])),
        "writes_count": len(step.get("writes", [])),
        "deletes_count": len(step.get("deletes", [])),
        "dds_count": len(step.get("dds", [])),
    }


def dd_items(step: dict[str, Any], wanted_access: set[str]) -> list[dict[str, Any]]:
    items = []
    for dd in step.get("dds", []):
        if not isinstance(dd, dict):
            continue
        access_type = str(dd.get("access_type", "")).lower()
        if access_type not in wanted_access:
            continue
        line = (dd.get("source_lines") or {}).get("start")
        items.append(
            {
                "job": step.get("job"),
                "step": step.get("step"),
                "program": step.get("program") or step.get("target"),
                "ddname": dd.get("ddname"),
                "dsn": dd.get("dsn"),
                "disp": dd.get("disp"),
                "sysout": dd.get("sysout"),
                "output": dd.get("output"),
                "dataset_kind": dd.get("dataset_kind"),
                "access_type": dd.get("access_type"),
                "access_reason": dd.get("access_reason"),
                "source_lines": dd.get("source_lines"),
                "citation": citation(step.get("__artifact_path") or "jcl", line=line, detail=str(dd.get("ddname", ""))),
            }
        )
    return items


def read_artifact(root: Path, kind: str) -> Any | None:
    for path in artifact_candidates(root, kind):
        payload = read_json(path)
        if payload is not None:
            return payload
    return None


def artifact_source(root: Path, kind: str) -> str:
    for path in artifact_candidates(root, kind):
        if path.is_file():
            return relative_path(root, path)
    return kind


def artifact_candidates(root: Path, kind: str) -> list[Path]:
    return [
        root / f"{kind}.json",
        root / kind / f"{kind}.json",
    ]


def iter_artifact_files(root: Path, kind: str) -> list[Path]:
    files = []
    nested = root / kind
    if nested.is_dir():
        files.extend(sorted(nested.glob(f"{kind}*.json")))
    files.extend(sorted(root.glob(f"{kind}*.json")))
    seen: set[str] = set()
    unique = []
    for path in files:
        key = str(path.resolve()).lower()
        if key not in seen and path.is_file():
            seen.add(key)
            unique.append(path)
    return unique


def read_json(path: Path) -> Any | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def artifact_program(payload: Any) -> str:
    if isinstance(payload, dict):
        return str(payload.get("program", "")).upper()
    return ""


def first_site_line(payload: dict[str, Any]) -> Any | None:
    evidence = payload.get("evidence", {})
    if not evidence and isinstance(payload.get("content"), dict):
        evidence = payload.get("content", {}).get("evidence", {})
    for key in ("write_sites", "read_sites", "control_sites"):
        for site in evidence.get(key, []):
            line = site.get("line_start")
            if isinstance(line, int) and line > 0:
                return line
    return None


def first_call_parameter_line(variable: dict[str, Any]) -> Any | None:
    for key in ("writes_before_call", "reads_before_call", "reads_after_call"):
        for site in variable.get(key, []):
            line = site.get("line_start")
            if isinstance(line, int) and line > 0:
                return line
    return None


def tokens_from_statement(statement: str) -> set[str]:
    return {
        token
        for token in re.findall(r"\b[A-Z][A-Z0-9-]{1,}\b", statement.upper())
        if "-" in token or token.startswith(("W", "PD", "TWCOB", "PX", "DFH", "SQL"))
    }


def screen_family(variable: str) -> str:
    variable = variable.upper()
    if len(variable) > 1 and variable[-1] in {"A", "F", "I", "L", "O"}:
        return variable[:-1]
    return variable


def is_cobol_keyword(token: str) -> bool:
    return token in {
        "AND",
        "END-IF",
        "EQUAL",
        "GREATER",
        "HIGH-VALUE",
        "IF",
        "MOVE",
        "NOT",
        "OR",
        "SPACES",
        "THEN",
        "TO",
    }


def positive_line(value: Any) -> bool:
    return isinstance(value, int) and value > 0


def citation(path: Any, line: Any | None = None, detail: str | None = None) -> str:
    parts = [str(path)]
    if line not in (None, "", -1):
        parts.append(f"line {line}")
    if detail:
        parts.append(str(detail))
    return " | ".join(parts)


def relative_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def unique_dicts(items: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for item in items:
        key = tuple(str(item.get(name, "")) for name in keys)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
