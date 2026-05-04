#!/usr/bin/env python3
import argparse
import copy
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


COMMENT_SECTION_HEADERS = {
    "REQUISITI": "requirements",
    "PRODOTTI": "products",
    "RIESECUZIONE": "rerun_notes",
}

CONTROL_DDNAMES = {
    "SYSIN",
    "STEPLIB",
    "JOBLIB",
    "SORTLIB",
    "JCLLIB",
    "SYSTSIN",
}

READ_DDNAMES = {"SORTIN", "INPUT", "INPSEQ", "SYSUT1"}
WRITE_DDNAMES = {"SORTOUT", "OUTPUT", "SYSUT2"}

CONTROL_OPERATIONS = {"IF", "ELSE", "ENDIF", "SET", "OUTPUT", "INCLUDE"}
STATEMENT_OPERATIONS = {
    "JOB",
    "EXEC",
    "DD",
    "PROC",
    "PEND",
    "JCLLIB",
    *CONTROL_OPERATIONS,
}

WARNING_KEYWORDS = (
    "NON RIESEGUIBILE",
    "ATTENZIONE",
    "VERIFICARE",
    "ABEND",
    "ERRORE",
    "ERROR",
    "WARNING",
)

PURPOSE_IGNORE_PREFIXES = (
    "REQUISITI",
    "PRODOTTI",
    "RIESECUZIONE",
    "MODIFICATO",
)


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Z0-9-]+", "_", (text or "").upper()).strip("_") or "ITEM"


def normalize_name(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    value = text.strip().upper()
    return value or None


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def unique_in_order(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def split_inline_comment(text: str) -> Tuple[str, List[str]]:
    notes: List[str] = []
    in_quote = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "'":
            in_quote = not in_quote
            i += 1
            continue
        if not in_quote and text.startswith("<==", i):
            note = normalize_spaces(text[i + 3 :])
            if note:
                notes.append(note)
            return text[:i].rstrip(), notes
        if not in_quote and text.startswith("**", i):
            note = normalize_spaces(text[i + 2 :])
            if note:
                notes.append(note)
            return text[:i].rstrip(), notes
        i += 1
    return text.rstrip(), notes


def split_continuation_note(text: str) -> Tuple[str, List[str]]:
    notes: List[str] = []
    in_quote = False
    i = 0
    while i < len(text) - 1:
        ch = text[i]
        if ch == "'":
            in_quote = not in_quote
            i += 1
            continue
        if not in_quote and text[i] == " " and text[i + 1] == " ":
            note = normalize_spaces(text[i:])
            if note:
                notes.append(note)
            return text[:i].rstrip(), notes
        i += 1
    return text.rstrip(), notes


def clean_comment_text(raw: str) -> str:
    text = raw[3:].strip()
    text = re.sub(r"^/+", "", text).strip()
    text = re.sub(r"\|+$", "", text).strip()
    return normalize_spaces(text)


def is_decorative_comment(text: str) -> bool:
    cleaned = re.sub(r"[\s*/|#=_.:-]+", "", text or "")
    return cleaned == ""


def looks_like_warning(text: str) -> bool:
    upper = (text or "").upper()
    return any(keyword in upper for keyword in WARNING_KEYWORDS)


def is_section_header(text: str) -> bool:
    upper = (text or "").upper().rstrip(":").strip()
    return any(upper.startswith(header) for header in COMMENT_SECTION_HEADERS)


def looks_like_commented_jcl(text: str) -> bool:
    upper = (text or "").upper().strip()
    if upper.startswith("***"):
        return True
    if upper.startswith(("RESTART=", "TYPRUN=", "COND=", "CLASS=", "MSGCLASS=", "MSGLEVEL=")):
        return True
    if upper.startswith("*") and any(
        token in upper
        for token in ("RESTART=", "TYPRUN=", "COND=", "CLASS=", "MSGCLASS=", "MSGLEVEL=")
    ):
        return True
    if upper.startswith("**MIGR ") or upper.startswith("*STEPLIB "):
        return True
    if upper.startswith("*") and " DD " in upper:
        return True
    if upper.startswith(
        (
            "LIBPROC ",
            "JOB ",
            "EXEC ",
            "PROC ",
            "PEND",
            "DD ",
            "DISP=",
            "VOL=",
            "DCB=",
            "UNIT=",
            "SYSOUT ",
            "SYSTSPRT ",
            "STEPLIB ",
        )
    ):
        return True
    return bool(re.match(r"^[A-Z0-9$#@-]+\s+(DD|EXEC|PROC|JOB)\b", upper))


def first_disp_status(disp: Optional[str]) -> str:
    if not disp:
        return ""
    normalized = disp.strip().upper()
    if normalized.startswith("(") and normalized.endswith(")"):
        normalized = normalized[1:-1]
    return normalized.split(",", 1)[0].strip()


def normalize_disp(disp: Optional[str]) -> str:
    return (disp or "").replace(" ", "").upper()


def split_top_level(text: str) -> List[str]:
    parts: List[str] = []
    buf: List[str] = []
    depth = 0
    in_quote = False

    for ch in text:
        if ch == "'":
            in_quote = not in_quote
            buf.append(ch)
            continue
        if not in_quote:
            if ch == "(":
                depth += 1
            elif ch == ")" and depth > 0:
                depth -= 1
            elif ch == "," and depth == 0:
                piece = "".join(buf).strip()
                if piece:
                    parts.append(piece)
                buf = []
                continue
        buf.append(ch)

    piece = "".join(buf).strip()
    if piece:
        parts.append(piece)
    return parts


def parse_operands(text: str) -> Tuple[List[str], Dict[str, str]]:
    positional: List[str] = []
    keyword: Dict[str, str] = {}

    for part in split_top_level(text):
        if "=" not in part:
            positional.append(part.strip())
            continue
        key, value = part.split("=", 1)
        value = value.strip()
        if not (value.startswith("'") and value.endswith("'")):
            value = re.split(r"\s{2,}", value, maxsplit=1)[0].strip()
        keyword[key.strip().upper()] = value

    return positional, keyword


def first_token(text: str) -> str:
    parts = (text or "").split(None, 1)
    return parts[0].upper() if parts else ""


def parse_jcl_comments(path: Path) -> List[Dict[str, Any]]:
    comments: List[Dict[str, Any]] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        line = raw.rstrip()
        if not line.startswith("//*"):
            continue
        text = clean_comment_text(line)
        comments.append(
            {
                "line": lineno,
                "text": text,
                "decorative": is_decorative_comment(text),
                "warning": looks_like_warning(text),
            }
        )
    return comments


def parse_jcl_statements(path: Path) -> List[Dict[str, Any]]:
    statements: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None

    for lineno, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        line = raw.rstrip()
        if not line or not line.startswith("//"):
            continue
        if line.startswith("//*"):
            continue

        body = line[2:]
        if current is not None and body[:1].isspace():
            text = body.strip()
            text, inline_notes = split_inline_comment(text)
            text, continuation_notes = split_continuation_note(text)
            notes = inline_notes + continuation_notes
            current_op = first_token(current.get("text", ""))
            incoming_op = first_token(text)

            if text and incoming_op == "DD" and current_op == "DD":
                current["annotations"] = unique_in_order(current["annotations"])
                statements.append(current)
                current = {
                    "label": current["label"],
                    "text": text,
                    "start_line": lineno,
                    "end_line": lineno,
                    "annotations": notes,
                    "implicit_label": True,
                }
                continue

            if text and incoming_op in CONTROL_OPERATIONS:
                current["annotations"] = unique_in_order(current["annotations"])
                statements.append(current)
                current = {
                    "label": "",
                    "text": text,
                    "start_line": lineno,
                    "end_line": lineno,
                    "annotations": notes,
                    "implicit_label": False,
                }
                continue

            if text:
                current["text"] = f"{current['text']} {text}".strip()
            if notes:
                current["annotations"].extend(notes)
            current["end_line"] = lineno
            continue

        name_field = body[:8]
        remainder = body[8:] if len(body) > 8 else ""
        label = name_field.strip().upper()
        text = remainder.strip()
        text, inline_notes = split_inline_comment(text)
        text, continuation_notes = split_continuation_note(text)
        notes = inline_notes + continuation_notes

        if not label and current is not None:
            current_op = first_token(current.get("text", ""))
            incoming_op = first_token(text)

            if text and incoming_op == "DD" and current_op == "DD":
                current["annotations"] = unique_in_order(current["annotations"])
                statements.append(current)
                current = {
                    "label": current["label"],
                    "text": text,
                    "start_line": lineno,
                    "end_line": lineno,
                    "annotations": notes,
                    "implicit_label": True,
                }
                continue

            if text and incoming_op in CONTROL_OPERATIONS:
                current["annotations"] = unique_in_order(current["annotations"])
                statements.append(current)
                current = {
                    "label": "",
                    "text": text,
                    "start_line": lineno,
                    "end_line": lineno,
                    "annotations": notes,
                    "implicit_label": False,
                }
                continue

            if text:
                current["text"] = f"{current['text']} {text}".strip()
            if notes:
                current["annotations"].extend(notes)
            current["end_line"] = lineno
            continue

        if current is not None:
            current["annotations"] = unique_in_order(current["annotations"])
            statements.append(current)

        current = {
            "label": label,
            "text": text,
            "start_line": lineno,
            "end_line": lineno,
            "annotations": notes,
            "implicit_label": False,
        }

    if current is not None:
        current["annotations"] = unique_in_order(current["annotations"])
        statements.append(current)

    return statements


def infer_dataset_kind(dsn: Optional[str]) -> Optional[str]:
    if not dsn:
        return None
    upper = dsn.upper()
    if upper.startswith("&&"):
        return "temporary"
    if upper.startswith("SYS1.") or upper.startswith("SYSOUT"):
        return "system"
    return "persistent"


def infer_access_type(dd: Dict[str, Any], step: Dict[str, Any]) -> Tuple[str, str]:
    ddname = normalize_name(dd.get("ddname")) or ""
    disp = normalize_disp(dd.get("disp"))
    status = first_disp_status(dd.get("disp"))
    raw = (dd.get("raw") or "").upper()
    dsn = dd.get("dsn")

    if dd.get("sysout"):
        return "sysout", "SYSOUT destination"

    if "DUMMY" in raw and not dsn:
        return "control", "DUMMY DD"

    if ddname in CONTROL_DDNAMES:
        return "control", "Control DD name"

    if step.get("program") == "IEFBR14" and "DELETE" in disp:
        return "delete", "IEFBR14 cleanup pattern"

    if ddname in READ_DDNAMES:
        return "read", "Input DD name"

    if ddname in WRITE_DDNAMES:
        return "write", "Output DD name"

    if status in {"OLD", "SHR"}:
        return "read", "DISP references an existing dataset"

    if status in {"NEW", "MOD"}:
        return "write", "DISP creates or updates a dataset"

    if disp.startswith("(,") or "(,CATLG" in disp or "(,PASS" in disp:
        return "write", "DISP implies dataset creation"

    if dsn:
        return "unknown", "Dataset present but access is ambiguous"

    return "control", "Non-dataset DD"


def collect_preceding_comments(
    comments: List[Dict[str, Any]],
    start_line: int,
    max_distance: int = 6,
    max_gap: int = 2,
) -> List[str]:
    window = [
        c
        for c in comments
        if not c["decorative"]
        and not looks_like_commented_jcl(c["text"])
        and c["line"] < start_line
        and start_line - c["line"] <= max_distance
    ]
    if not window:
        return []

    block: List[str] = []
    prev_line = start_line
    for comment in reversed(window):
        if prev_line - comment["line"] > max_gap:
            break
        block.append(comment["text"])
        prev_line = comment["line"]
    return list(reversed(block))


def extract_comment_sections(comments: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    sections = {value: [] for value in COMMENT_SECTION_HEADERS.values()}
    current: Optional[str] = None

    for comment in comments:
        if comment["decorative"]:
            continue
        text = comment["text"]
        upper = text.upper().rstrip(":").strip()

        if upper.startswith("MODIFICATO"):
            current = None
            continue

        matched_header = None
        for header, key in COMMENT_SECTION_HEADERS.items():
            if upper.startswith(header):
                matched_header = key
                break

        if matched_header:
            current = matched_header
            continue

        if current and text.startswith("-"):
            item = text.lstrip("- ").strip()
            if item:
                sections[current].append(item)
            continue

        if current and sections[current] and not looks_like_commented_jcl(text):
            sections[current][-1] = f"{sections[current][-1]} {text}".strip()
            continue

        if current and not text.startswith("-"):
            current = None

    return sections


def extract_purpose(comments: List[Dict[str, Any]]) -> Optional[str]:
    for comment in comments:
        if comment["decorative"]:
            continue
        text = comment["text"]
        upper = text.upper()
        if text.startswith("-"):
            continue
        if is_section_header(text):
            continue
        if looks_like_commented_jcl(text):
            continue
        if any(upper.startswith(prefix) for prefix in PURPOSE_IGNORE_PREFIXES):
            continue
        if looks_like_warning(text):
            continue
        return text
    return None


def extract_comment_highlights(comments: List[Dict[str, Any]], limit: int = 8) -> List[str]:
    highlights: List[str] = []
    for comment in comments:
        if comment["decorative"]:
            continue
        text = comment["text"]
        if looks_like_commented_jcl(text):
            continue
        if text.upper().startswith("MODIFICATO"):
            continue
        highlights.append(text)
        if len(highlights) >= limit:
            break
    return highlights


def summarize_step_dds(dds: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    by_access: Dict[str, List[str]] = defaultdict(list)
    sysouts: List[str] = []

    for dd in dds:
        access_type = dd.get("access_type")
        dsn = dd.get("dsn")
        if access_type == "sysout":
            sysouts.append(dd.get("ddname") or "SYSOUT")
            continue
        if not dsn:
            continue
        by_access[access_type].append(dsn)

    return {
        "reads": unique_in_order(by_access.get("read", [])),
        "writes": unique_in_order(by_access.get("write", [])),
        "deletes": unique_in_order(by_access.get("delete", [])),
        "controls": unique_in_order(by_access.get("control", [])),
        "unknowns": unique_in_order(by_access.get("unknown", [])),
        "sysouts": unique_in_order(sysouts),
    }


def annotate_steps(steps: List[Dict[str, Any]], comments: List[Dict[str, Any]]) -> None:
    for step in steps:
        step["annotations"] = unique_in_order(step.get("annotations", []))
        step["comment_context"] = collect_preceding_comments(
            comments, step["source_lines"]["start"]
        )
        for dd in step["dds"]:
            dd["dataset_kind"] = infer_dataset_kind(dd.get("dsn"))
            dd["is_temporary"] = dd["dataset_kind"] == "temporary"
            access_type, access_reason = infer_access_type(dd, step)
            dd["access_type"] = access_type
            dd["access_reason"] = access_reason
        step.update(summarize_step_dds(step["dds"]))


def build_execution_steps(
    steps: List[Dict[str, Any]],
    proc_defs: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    execution_steps: List[Dict[str, Any]] = []
    order = 1

    for step in steps:
        if step["scope"] != "job":
            continue

        if step.get("exec_kind") == "procedure" and step.get("resolved_locally"):
            proc_def = proc_defs.get(step.get("proc") or "")
            if not proc_def:
                continue
            for proc_step in proc_def["steps"]:
                expanded = copy.deepcopy(proc_step)
                expanded["execution_order"] = order
                expanded["execution_scope"] = "expanded_local_procedure"
                expanded["invoked_by_step"] = step["step"]
                expanded["invoked_proc"] = step.get("proc")
                expanded["invocation_parameters"] = step.get("parameters", {})
                execution_steps.append(expanded)
                order += 1
            continue

        direct = copy.deepcopy(step)
        direct["execution_order"] = order
        direct["execution_scope"] = "job"
        direct["invoked_by_step"] = None
        direct["invoked_proc"] = None
        direct["invocation_parameters"] = step.get("parameters", {})
        execution_steps.append(direct)
        order += 1

    return execution_steps


def build_dataset_catalog(execution_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    datasets_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for step in execution_steps:
        for dd in step["dds"]:
            dsn = dd.get("dsn")
            if not dsn:
                continue

            datasets_map[dsn].append(
                {
                    "execution_order": step["execution_order"],
                    "step": step["step"],
                    "ddname": dd["ddname"],
                    "program": step.get("program"),
                    "proc": step.get("proc"),
                    "exec_kind": step.get("exec_kind"),
                    "scope": step.get("execution_scope"),
                    "access_type": dd.get("access_type"),
                    "access_reason": dd.get("access_reason"),
                    "dataset_kind": dd.get("dataset_kind"),
                    "disp": dd.get("disp"),
                    "invoked_by_step": step.get("invoked_by_step"),
                    "invoked_proc": step.get("invoked_proc"),
                }
            )

    datasets: List[Dict[str, Any]] = []
    for dsn, usages in sorted(datasets_map.items()):
        ordered = sorted(usages, key=lambda item: item["execution_order"])
        producers = [u for u in ordered if u["access_type"] == "write"]
        consumers = [u for u in ordered if u["access_type"] == "read"]
        controllers = [u for u in ordered if u["access_type"] == "control"]
        deleters = [u for u in ordered if u["access_type"] == "delete"]
        first_write_order = min((u["execution_order"] for u in producers), default=None)
        external_input = any(
            u["access_type"] in {"read", "control"}
            and (first_write_order is None or u["execution_order"] < first_write_order)
            for u in ordered
        )

        datasets.append(
            {
                "dsn": dsn,
                "dataset_kind": next(
                    (u["dataset_kind"] for u in ordered if u.get("dataset_kind")),
                    None,
                ),
                "external_input": external_input,
                "produced_by": producers,
                "consumed_by": consumers,
                "controlled_by": controllers,
                "deleted_by": deleters,
                "used_by": ordered,
            }
        )

    return datasets


def build_flow(job: str, source: str, data: Dict[str, Any]) -> Dict[str, Any]:
    edges: List[Dict[str, Any]] = []
    seen_edges = set()
    dataset_timelines: List[Dict[str, Any]] = []

    for dataset in data["datasets"]:
        usages = dataset["used_by"]
        timeline = [
            {
                "execution_order": usage["execution_order"],
                "step": usage["step"],
                "ddname": usage["ddname"],
                "program": usage["program"],
                "proc": usage["proc"],
                "access_type": usage["access_type"],
            }
            for usage in usages
        ]
        dataset_timelines.append(
            {
                "dsn": dataset["dsn"],
                "dataset_kind": dataset["dataset_kind"],
                "external_input": dataset["external_input"],
                "timeline": timeline,
            }
        )

        last_writer: Optional[Dict[str, Any]] = None
        for usage in usages:
            if usage["access_type"] == "write":
                last_writer = usage
                continue

            if usage["access_type"] == "read" and last_writer:
                edge = (
                    last_writer["step"],
                    usage["step"],
                    dataset["dsn"],
                    "produces_input_for",
                )
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    edges.append(
                        {
                            "from_step": last_writer["step"],
                            "to_step": usage["step"],
                            "dsn": dataset["dsn"],
                            "flow_type": "produces_input_for",
                        }
                    )
                continue

            if usage["access_type"] == "delete" and last_writer:
                edge = (
                    last_writer["step"],
                    usage["step"],
                    dataset["dsn"],
                    "deleted_after",
                )
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    edges.append(
                        {
                            "from_step": last_writer["step"],
                            "to_step": usage["step"],
                            "dsn": dataset["dsn"],
                            "flow_type": "deleted_after",
                        }
                    )

    return {
        "type": "jcl.flow",
        "job": job,
        "source": source,
        "purpose": data.get("purpose"),
        "warnings": data.get("warnings", []),
        "execution_steps": [
            {
                "execution_order": step["execution_order"],
                "step": step["step"],
                "execution_scope": step["execution_scope"],
                "invoked_by_step": step.get("invoked_by_step"),
                "invoked_proc": step.get("invoked_proc"),
                "exec_kind": step.get("exec_kind"),
                "target": step.get("target"),
                "program": step.get("program"),
                "proc": step.get("proc"),
                "parameters": step.get("parameters", {}),
                "reads": step.get("reads", []),
                "writes": step.get("writes", []),
                "deletes": step.get("deletes", []),
                "controls": step.get("controls", []),
                "unknowns": step.get("unknowns", []),
                "notes": step.get("annotations", []),
                "comment_context": step.get("comment_context", []),
            }
            for step in data["execution_steps"]
        ],
        "datasets": dataset_timelines,
        "edges": edges,
    }


def preview(items: List[str], limit: int = 4) -> str:
    values = [item for item in items if item]
    if not values:
        return "none"
    if len(values) <= limit:
        return ", ".join(values)
    return ", ".join(values[:limit]) + f" (+{len(values) - limit} more)"


def build_rag_documents(job: str, source: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    purpose = data.get("purpose") or f"JCL job {job}"
    warnings = data.get("warnings", [])
    programs = data.get("programs", [])
    unresolved = data.get("unresolved_procedures", [])

    docs.append(
        {
            "id": f"JCL-JOB-{safe_name(job)}",
            "type": "jcl_job",
            "job": job,
            "source": source,
            "embedding_text": (
                f"JCL job {job}. Purpose: {purpose}. Programs: {preview(programs)}. "
                f"Execution steps: {len(data.get('execution_steps', []))}. "
                f"Warnings: {preview(warnings, limit=3)}. "
                f"Unresolved procedures: {preview(unresolved)}."
            ),
            "content": {
                "purpose": data.get("purpose"),
                "programs": programs,
                "warnings": warnings,
                "unresolved_procedures": unresolved,
                "requirements": data.get("comment_sections", {}).get("requirements", []),
                "products": data.get("comment_sections", {}).get("products", []),
                "rerun_notes": data.get("comment_sections", {}).get("rerun_notes", []),
            },
        }
    )

    for step in data.get("execution_steps", []):
        target = step.get("program") or step.get("proc") or "UNKNOWN"
        docs.append(
            {
                "id": f"JCL-STEP-{safe_name(job)}-{safe_name(step['step'])}",
                "type": "jcl_step",
                "job": job,
                "source": source,
                "embedding_text": (
                    f"JCL job {job} step {step['step']} executes {target}. "
                    f"Reads: {preview(step.get('reads', []))}. "
                    f"Writes: {preview(step.get('writes', []))}. "
                    f"Deletes: {preview(step.get('deletes', []))}. "
                    f"Controls: {preview(step.get('controls', []))}. "
                    f"Notes: {preview(step.get('comment_context', []) + step.get('annotations', []), limit=3)}."
                ),
                "content": {
                    "execution_order": step.get("execution_order"),
                    "step": step["step"],
                    "program": step.get("program"),
                    "proc": step.get("proc"),
                    "reads": step.get("reads", []),
                    "writes": step.get("writes", []),
                    "deletes": step.get("deletes", []),
                    "controls": step.get("controls", []),
                    "notes": step.get("annotations", []),
                    "comment_context": step.get("comment_context", []),
                },
            }
        )

    for dataset in data.get("datasets", []):
        docs.append(
            {
                "id": f"JCL-DSN-{safe_name(job)}-{safe_name(dataset['dsn'])}",
                "type": "jcl_dataset",
                "job": job,
                "source": source,
                "embedding_text": (
                    f"JCL job {job} dataset {dataset['dsn']} ({dataset.get('dataset_kind') or 'unknown kind'}). "
                    f"Produced by: {preview([u['step'] for u in dataset.get('produced_by', [])])}. "
                    f"Consumed by: {preview([u['step'] for u in dataset.get('consumed_by', [])])}. "
                    f"Deleted by: {preview([u['step'] for u in dataset.get('deleted_by', [])])}. "
                    f"External input: {'yes' if dataset.get('external_input') else 'no'}."
                ),
                "content": {
                    "dsn": dataset["dsn"],
                    "dataset_kind": dataset.get("dataset_kind"),
                    "external_input": dataset.get("external_input"),
                    "produced_by": dataset.get("produced_by", []),
                    "consumed_by": dataset.get("consumed_by", []),
                    "controlled_by": dataset.get("controlled_by", []),
                    "deleted_by": dataset.get("deleted_by", []),
                },
            }
        )

    for idx, warning in enumerate(warnings, start=1):
        docs.append(
            {
                "id": f"JCL-WARN-{safe_name(job)}-{idx:03d}",
                "type": "jcl_warning",
                "job": job,
                "source": source,
                "embedding_text": f"JCL job {job} warning: {warning}",
                "content": {"warning": warning},
            }
        )

    return docs


def parse_dd(stmt: Dict[str, Any]) -> Dict[str, Any]:
    _, keyword = parse_operands(stmt["operands"])
    return {
        "ddname": stmt["label"],
        "concatenated": bool(stmt.get("implicit_label")),
        "dsn": keyword.get("DSN"),
        "disp": keyword.get("DISP"),
        "sysout": keyword.get("SYSOUT"),
        "unit": keyword.get("UNIT"),
        "output": keyword.get("OUTPUT"),
        "raw": stmt["text"],
        "annotations": stmt.get("annotations", []),
        "source_lines": {
            "start": stmt["start_line"],
            "end": stmt["end_line"],
        },
    }


def parse_exec(stmt: Dict[str, Any], current_proc: Optional[str]) -> Dict[str, Any]:
    positional, keyword = parse_operands(stmt["operands"])
    program = normalize_name(keyword.get("PGM"))
    proc = normalize_name(keyword.get("PROC"))
    exec_kind = "unknown"
    target = None

    if program:
        exec_kind = "program"
        target = program
    elif proc:
        exec_kind = "procedure"
        target = proc
    elif positional:
        proc = normalize_name(positional[0])
        exec_kind = "procedure"
        target = proc

    parameters = {k: v for k, v in keyword.items() if k not in {"PGM", "PROC"}}

    return {
        "step": stmt["label"],
        "scope": "procedure_definition" if current_proc else "job",
        "defined_in_proc": current_proc,
        "exec_kind": exec_kind,
        "target": target,
        "program": program,
        "proc": proc,
        "parameters": parameters,
        "positional": positional[1:] if positional and proc else positional,
        "dds": [],
        "raw": stmt["text"],
        "annotations": stmt.get("annotations", []),
        "source_lines": {
            "start": stmt["start_line"],
            "end": stmt["end_line"],
        },
    }


def parse_jcl(path: Path) -> Dict[str, Any]:
    statements = parse_jcl_statements(path)
    comments = parse_jcl_comments(path)
    job_name = None
    jcllib_order: List[str] = []
    symbols: Dict[str, str] = {}
    steps: List[Dict[str, Any]] = []
    control_statements: List[Dict[str, Any]] = []
    proc_defs: Dict[str, Dict[str, Any]] = {}
    current_proc: Optional[str] = None
    current_step: Optional[Dict[str, Any]] = None

    for raw_stmt in statements:
        text = raw_stmt["text"]
        if not text:
            current_step = None
            continue

        parts = text.split(None, 1)
        operation = parts[0].upper()
        operands = parts[1].strip() if len(parts) > 1 else ""
        stmt = dict(raw_stmt)
        stmt["operation"] = operation
        stmt["operands"] = operands

        if operation == "JOB":
            job_name = stmt["label"] or job_name
            current_step = None
            continue

        if operation == "JCLLIB":
            _, keyword = parse_operands(operands)
            order = keyword.get("ORDER")
            if order:
                jcllib_order.extend(
                    [item.strip() for item in split_top_level(order) if item.strip()]
                )
            current_step = None
            continue

        if operation == "SET":
            _, keyword = parse_operands(operands)
            symbols.update(keyword)
            control_statements.append(
                {
                    "label": stmt["label"],
                    "operation": operation,
                    "operands": operands,
                    "parameters": keyword,
                    "scope": "procedure_definition" if current_proc else "job",
                    "defined_in_proc": current_proc,
                    "source_lines": {
                        "start": stmt["start_line"],
                        "end": stmt["end_line"],
                    },
                }
            )
            current_step = None
            continue

        if operation == "PROC":
            proc_name = stmt["label"] or normalize_name(operands) or "PROC"
            _, defaults = parse_operands(operands)
            proc_defs[proc_name] = {
                "procedure": proc_name,
                "parameters": defaults,
                "steps": [],
                "source_lines": {
                    "start": stmt["start_line"],
                    "end": stmt["end_line"],
                },
            }
            current_proc = proc_name
            current_step = None
            continue

        if operation == "PEND":
            if current_proc and current_proc in proc_defs:
                proc_defs[current_proc]["source_lines"]["end"] = stmt["end_line"]
            current_proc = None
            current_step = None
            continue

        if operation == "EXEC":
            current_step = parse_exec(stmt, current_proc=current_proc)
            steps.append(current_step)
            if current_proc and current_proc in proc_defs:
                proc_defs[current_proc]["steps"].append(current_step)
                proc_defs[current_proc]["source_lines"]["end"] = stmt["end_line"]
            continue

        if operation == "DD" and current_step is not None:
            current_step["dds"].append(parse_dd(stmt))
            if current_proc and current_proc in proc_defs:
                proc_defs[current_proc]["source_lines"]["end"] = stmt["end_line"]
            continue

        if operation in CONTROL_OPERATIONS:
            control_statements.append(
                {
                    "label": stmt["label"],
                    "operation": operation,
                    "operands": operands,
                    "parameters": {},
                    "scope": "procedure_definition" if current_proc else "job",
                    "defined_in_proc": current_proc,
                    "source_lines": {
                        "start": stmt["start_line"],
                        "end": stmt["end_line"],
                    },
                }
            )
            current_step = None
            continue

        current_step = None

    for step in steps:
        proc_def = proc_defs.get(step.get("proc") or "")
        if proc_def:
            step["resolved_locally"] = True
            step["resolved_proc_steps"] = [s["step"] for s in proc_def["steps"]]
            step["resolved_proc_programs"] = sorted(
                {s["program"] for s in proc_def["steps"] if s.get("program")}
            )
        else:
            step["resolved_locally"] = False
            step["resolved_proc_steps"] = []
            step["resolved_proc_programs"] = []

    annotate_steps(steps, comments)
    execution_steps = build_execution_steps(steps, proc_defs)
    datasets = build_dataset_catalog(execution_steps)

    local_procedures: List[Dict[str, Any]] = []
    for proc_name, proc_def in proc_defs.items():
        local_procedures.append(
            {
                "procedure": proc_name,
                "parameters": proc_def["parameters"],
                "steps_count": len(proc_def["steps"]),
                "programs": sorted(
                    {s["program"] for s in proc_def["steps"] if s.get("program")}
                ),
                "source_lines": proc_def["source_lines"],
            }
        )

    programs = sorted({step["program"] for step in steps if step.get("program")})
    procedures = sorted(
        {step["proc"] for step in steps if step.get("proc")} | set(proc_defs.keys())
    )
    procedure_invocations = [
        {
            "step": step["step"],
            "proc": step["proc"],
            "resolved_locally": step["resolved_locally"],
            "resolved_proc_programs": step["resolved_proc_programs"],
            "parameters": step["parameters"],
        }
        for step in steps
        if step.get("proc")
    ]
    unresolved_procedures = unique_in_order(
        [step["proc"] for step in steps if step.get("proc") and not step["resolved_locally"]]
    )

    comment_sections = extract_comment_sections(comments)
    purpose = extract_purpose(comments)
    comment_highlights = extract_comment_highlights(comments)
    warnings = unique_in_order(
        [comment["text"].lstrip("- ").strip() for comment in comments if comment["warning"]]
        + [
            f"{step['step']}: {note}"
            for step in steps
            for note in step.get("annotations", [])
            if looks_like_warning(note)
        ]
        + [f"Unresolved procedure invocation: {proc}" for proc in unresolved_procedures]
    )

    data = {
        "job_name": job_name or path.stem.upper(),
        "purpose": purpose,
        "warnings": warnings,
        "comment_highlights": comment_highlights,
        "comment_sections": comment_sections,
        "jcllib_order": sorted(set(jcllib_order)),
        "symbols": symbols,
        "programs": programs,
        "procedures": procedures,
        "local_procedures": local_procedures,
        "procedure_invocations": procedure_invocations,
        "unresolved_procedures": unresolved_procedures,
        "control_statements": control_statements,
        "steps": steps,
        "execution_steps": execution_steps,
        "datasets": datasets,
        "proc_defs": proc_defs,
    }
    data["flow"] = build_flow(data["job_name"], str(path), data)
    data["rag_documents"] = build_rag_documents(data["job_name"], str(path), data)
    return data


def main():
    ap = argparse.ArgumentParser(description="Build JCL artifacts from a .jcl file")
    ap.add_argument("--jcl", required=True, help="Path to JCL file")
    ap.add_argument("--output-dir", required=True, help="Output directory for JCL artifacts")
    args = ap.parse_args()

    jcl_path = Path(args.jcl)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    data = parse_jcl(jcl_path)
    job = data["job_name"]
    source = str(jcl_path)

    summary = {
        "type": "jcl.summary",
        "job": job,
        "source": source,
        "purpose": data["purpose"],
        "warnings": data["warnings"],
        "comment_highlights": data["comment_highlights"],
        "requirements": data["comment_sections"]["requirements"],
        "products": data["comment_sections"]["products"],
        "rerun_notes": data["comment_sections"]["rerun_notes"],
        "programs": data["programs"],
        "procedures": data["procedures"],
        "unresolved_procedures": data["unresolved_procedures"],
        "jcllib_order": data["jcllib_order"],
        "symbols": data["symbols"],
        "local_procedures": data["local_procedures"],
        "procedure_invocations": data["procedure_invocations"],
        "control_statements_count": len(data["control_statements"]),
        "steps_count": len(data["steps"]),
        "execution_steps_count": len(data["execution_steps"]),
        "datasets_count": len(data["datasets"]),
        "external_inputs_count": sum(
            1 for dataset in data["datasets"] if dataset["external_input"]
        ),
    }

    (out_dir / "jcl.summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "jcl.flow.json").write_text(
        json.dumps(data["flow"], indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "jcl.rag_documents.json").write_text(
        json.dumps(data["rag_documents"], indent=2, ensure_ascii=False), encoding="utf-8"
    )

    for proc_name, proc_def in data["proc_defs"].items():
        doc = {
            "type": "jcl.procedures",
            "job": job,
            "procedure": proc_name,
            "parameters": proc_def["parameters"],
            "programs": sorted(
                {step["program"] for step in proc_def["steps"] if step.get("program")}
            ),
            "steps": [
                {
                    "step": step["step"],
                    "exec_kind": step["exec_kind"],
                    "target": step["target"],
                    "program": step["program"],
                    "proc": step["proc"],
                    "reads": step.get("reads", []),
                    "writes": step.get("writes", []),
                    "deletes": step.get("deletes", []),
                    "controls": step.get("controls", []),
                    "notes": step.get("annotations", []),
                }
                for step in proc_def["steps"]
            ],
            "source_lines": proc_def["source_lines"],
            "source": source,
        }
        fname = f"jcl.procedures.{safe_name(proc_name)}.json"
        (out_dir / fname).write_text(
            json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    for step in data["steps"]:
        fname = f"jcl.steps.{safe_name(step['step'])}.json"
        doc = {
            "type": "jcl.steps",
            "job": job,
            "step": step["step"],
            "scope": step["scope"],
            "defined_in_proc": step.get("defined_in_proc"),
            "exec_kind": step.get("exec_kind"),
            "target": step.get("target"),
            "program": step.get("program"),
            "proc": step.get("proc"),
            "parameters": step.get("parameters", {}),
            "positional": step.get("positional", []),
            "notes": step.get("annotations", []),
            "comment_context": step.get("comment_context", []),
            "reads": step.get("reads", []),
            "writes": step.get("writes", []),
            "deletes": step.get("deletes", []),
            "controls": step.get("controls", []),
            "unknowns": step.get("unknowns", []),
            "dds": step.get("dds", []),
            "resolved_locally": step.get("resolved_locally", False),
            "resolved_proc_steps": step.get("resolved_proc_steps", []),
            "resolved_proc_programs": step.get("resolved_proc_programs", []),
            "source_lines": step.get("source_lines"),
            "source": source,
        }
        (out_dir / fname).write_text(
            json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    for dataset in data["datasets"]:
        dsn = dataset["dsn"]
        fname = f"jcl.datasets.{safe_name(dsn)}.json"
        doc = {
            "type": "jcl.datasets",
            "job": job,
            "dsn": dsn,
            "dataset_kind": dataset["dataset_kind"],
            "external_input": dataset["external_input"],
            "produced_by": dataset["produced_by"],
            "consumed_by": dataset["consumed_by"],
            "controlled_by": dataset["controlled_by"],
            "deleted_by": dataset["deleted_by"],
            "used_by": dataset["used_by"],
            "source": source,
        }
        (out_dir / fname).write_text(
            json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    print(f"[OK] Wrote JCL artifacts to {out_dir}")


if __name__ == "__main__":
    main()
