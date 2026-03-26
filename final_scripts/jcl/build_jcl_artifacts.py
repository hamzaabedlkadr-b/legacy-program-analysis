#!/usr/bin/env python3
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Z0-9-]+", "_", (text or "").upper()).strip("_") or "ITEM"


def normalize_name(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    value = text.strip().upper()
    return value or None


def strip_inline_comment(text: str) -> str:
    in_quote = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "'":
            in_quote = not in_quote
            i += 1
            continue
        if not in_quote and text.startswith("**", i):
            return text[:i].rstrip()
        if not in_quote and text.startswith("<==", i):
            return text[:i].rstrip()
        i += 1
    return text.rstrip()


def strip_continuation_note(text: str) -> str:
    in_quote = False
    i = 0
    while i < len(text) - 1:
        ch = text[i]
        if ch == "'":
            in_quote = not in_quote
        if not in_quote and text[i] == " " and text[i + 1] == " ":
            return text[:i].rstrip()
        i += 1
    return text.rstrip()


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
            text = strip_continuation_note(strip_inline_comment(body.strip()))
            if text:
                current["text"] = f"{current['text']} {text}".strip()
                current["end_line"] = lineno
            continue

        name_field = body[:8]
        remainder = body[8:] if len(body) > 8 else ""
        label = name_field.strip().upper()
        text = strip_inline_comment(remainder.strip())

        if not label and current is not None:
            if text:
                current["text"] = f"{current['text']} {text}".strip()
                current["end_line"] = lineno
            continue

        if current is not None:
            statements.append(current)

        current = {
            "label": label,
            "text": text,
            "start_line": lineno,
            "end_line": lineno,
        }

    if current is not None:
        statements.append(current)

    return statements


def parse_dd(stmt: Dict[str, Any]) -> Dict[str, Any]:
    _, keyword = parse_operands(stmt["operands"])
    return {
        "ddname": stmt["label"],
        "dsn": keyword.get("DSN"),
        "disp": keyword.get("DISP"),
        "sysout": keyword.get("SYSOUT"),
        "unit": keyword.get("UNIT"),
        "output": keyword.get("OUTPUT"),
        "raw": stmt["text"],
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

    parameters = {
        k: v for k, v in keyword.items()
        if k not in {"PGM", "PROC"}
    }

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
        "source_lines": {
            "start": stmt["start_line"],
            "end": stmt["end_line"],
        },
    }


def parse_jcl(path: Path) -> Dict[str, Any]:
    statements = parse_jcl_statements(path)
    job_name = None
    jcllib_order: List[str] = []
    steps: List[Dict[str, Any]] = []
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
                jcllib_order.extend([item.strip() for item in split_top_level(order) if item.strip()])
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

        current_step = None

    datasets_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for step in steps:
        proc_def = proc_defs.get(step.get("proc") or "")
        if proc_def:
            step["resolved_locally"] = True
            step["resolved_proc_steps"] = [s["step"] for s in proc_def["steps"]]
            step["resolved_proc_programs"] = sorted({
                s["program"] for s in proc_def["steps"] if s.get("program")
            })
        else:
            step["resolved_locally"] = False
            step["resolved_proc_steps"] = []
            step["resolved_proc_programs"] = []

        for dd in step["dds"]:
            dsn = dd.get("dsn")
            if not dsn:
                continue
            datasets_map[dsn].append({
                "step": step["step"],
                "ddname": dd["ddname"],
                "program": step.get("program"),
                "proc": step.get("proc"),
                "exec_kind": step.get("exec_kind"),
                "scope": step.get("scope"),
            })

    local_procedures: List[Dict[str, Any]] = []
    for proc_name, proc_def in proc_defs.items():
        local_procedures.append({
            "procedure": proc_name,
            "parameters": proc_def["parameters"],
            "steps_count": len(proc_def["steps"]),
            "programs": sorted({
                s["program"] for s in proc_def["steps"] if s.get("program")
            }),
            "source_lines": proc_def["source_lines"],
        })

    datasets = [
        {"dsn": dsn, "used_by": usages}
        for dsn, usages in sorted(datasets_map.items())
    ]
    programs = sorted({
        step["program"] for step in steps if step.get("program")
    })
    procedures = sorted({
        step["proc"] for step in steps if step.get("proc")
    } | set(proc_defs.keys()))
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

    return {
        "job_name": job_name or path.stem.upper(),
        "jcllib_order": sorted(set(jcllib_order)),
        "programs": programs,
        "procedures": procedures,
        "local_procedures": local_procedures,
        "procedure_invocations": procedure_invocations,
        "steps": steps,
        "datasets": datasets,
        "proc_defs": proc_defs,
    }


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

    summary = {
        "type": "jcl.summary",
        "job": job,
        "source": str(jcl_path),
        "programs": data["programs"],
        "procedures": data["procedures"],
        "jcllib_order": data["jcllib_order"],
        "local_procedures": data["local_procedures"],
        "procedure_invocations": data["procedure_invocations"],
        "steps_count": len(data["steps"]),
        "datasets_count": len(data["datasets"]),
    }

    (out_dir / "jcl.summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    for proc_name, proc_def in data["proc_defs"].items():
        doc = {
            "type": "jcl.procedures",
            "job": job,
            "procedure": proc_name,
            "parameters": proc_def["parameters"],
            "programs": sorted({
                step["program"] for step in proc_def["steps"] if step.get("program")
            }),
            "steps": [
                {
                    "step": step["step"],
                    "exec_kind": step["exec_kind"],
                    "target": step["target"],
                    "program": step["program"],
                    "proc": step["proc"],
                }
                for step in proc_def["steps"]
            ],
            "source_lines": proc_def["source_lines"],
            "source": str(jcl_path),
        }
        fname = f"jcl.procedures.{safe_name(proc_name)}.json"
        (out_dir / fname).write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")

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
            "dds": step.get("dds", []),
            "resolved_locally": step.get("resolved_locally", False),
            "resolved_proc_steps": step.get("resolved_proc_steps", []),
            "resolved_proc_programs": step.get("resolved_proc_programs", []),
            "source_lines": step.get("source_lines"),
            "source": str(jcl_path),
        }
        (out_dir / fname).write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")

    for dataset in data["datasets"]:
        dsn = dataset["dsn"]
        fname = f"jcl.datasets.{safe_name(dsn)}.json"
        doc = {
            "type": "jcl.datasets",
            "job": job,
            "dsn": dsn,
            "used_by": dataset["used_by"],
            "source": str(jcl_path),
        }
        (out_dir / fname).write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[OK] Wrote JCL artifacts to {out_dir}")


if __name__ == "__main__":
    main()
