#!/usr/bin/env python3
"""Cross-check derived artifacts against the physical source map.

Every other artifact *describes* the program; program.source_lines.jsonl *is*
the program, line for line. That makes it an independent oracle: facts derived
by the extractors can be re-derived from it and compared, so a silent
extraction gap shows up as a discrepancy instead of as a confidently wrong
answer downstream.

This is deliberately not a test of one variable or one program. It states
invariants that must hold for any analyzed COBOL program and reports every
place they do not.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, NamedTuple, Set


class Statement(NamedTuple):
    line: int
    paragraph: str
    normalized: str
    raw: str


# Same literal shapes the literal-assignment builder recognises.
MOVE_LITERAL_RE = re.compile(
    r"(?<![A-Z0-9-])MOVE\s+(?P<literal>'[^']*'|\"[^\"]*\"|[+-]?\d+(?:\.\d+)?)"
    r"\s+TO\s+(?P<target>[A-Z][A-Z0-9-]+)(?![A-Z0-9-])",
    re.IGNORECASE,
)

MOVE_ANY_RE = re.compile(
    r"(?<![A-Z0-9-])MOVE\s+.+?\s+TO\s+(?P<target>[A-Z][A-Z0-9-]+)(?![A-Z0-9-])",
    re.IGNORECASE,
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_source_lines(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if raw:
                rows.append(json.loads(raw))
    return rows


def code_area(row: Dict[str, Any]) -> str:
    """Columns 8-72 of a fixed-format record, with column alignment preserved.

    The `normalized` field collapses runs of spaces, which silently rewrites the
    contents of quoted literals ('   IMPIANTO' becomes ' IMPIANTO'). Literal
    comparison must read the raw record instead.
    """
    text = str(row.get("text") or "")
    return text[7:72].rstrip() if len(text) > 7 else text.rstrip()


def procedure_statements(rows: Iterable[Dict[str, Any]]) -> List[Statement]:
    """Yield PROCEDURE DIVISION statements, folding continuation lines.

    Each statement carries both the normalized form (for structure) and the raw
    code area (for anything that inspects literal contents).
    """
    statements: List[Statement] = []
    for row in rows:
        if row.get("division") != "PROCEDURE DIVISION":
            continue
        if row.get("is_comment") or row.get("is_blank"):
            continue
        text = str(row.get("normalized") or "").strip()
        if not text:
            continue
        raw = code_area(row)
        if row.get("is_continuation") and statements:
            previous = statements[-1]
            statements[-1] = Statement(
                previous.line,
                previous.paragraph,
                f"{previous.normalized} {text}",
                f"{previous.raw} {raw.lstrip()}",
            )
            continue
        statements.append(
            Statement(
                int(row.get("line") or 0),
                str(row.get("paragraph") or ""),
                text,
                raw,
            )
        )
    return statements


def source_paragraphs(rows: Iterable[Dict[str, Any]]) -> Set[str]:
    """Paragraph names the physical source map attributes to PROCEDURE code."""
    return {
        str(row.get("paragraph")).upper()
        for row in rows
        if row.get("paragraph") and row.get("division") == "PROCEDURE DIVISION"
    }


def variable_evidence(used_variables: Any) -> Dict[str, Dict[str, Set[int]]]:
    variables = (
        used_variables.get("variables")
        if isinstance(used_variables, dict)
        else used_variables
    ) or []
    evidence: Dict[str, Dict[str, Set[int]]] = {}
    for variable in variables:
        name = str(variable.get("variable") or "").upper()
        if not name:
            continue
        sites = variable.get("evidence") or {}
        record = evidence.setdefault(name, {"write": set(), "read": set()})
        for kind, key in (("write_sites", "write"), ("read_write_sites", "write"),
                          ("read_sites", "read")):
            for site in sites.get(kind) or []:
                line = site.get("line_start") or site.get("line")
                if line:
                    record[key].add(int(line))
    return evidence


def site_paragraphs(used_variables: Any) -> Set[str]:
    variables = (
        used_variables.get("variables")
        if isinstance(used_variables, dict)
        else used_variables
    ) or []
    found: Set[str] = set()
    for variable in variables:
        sites = variable.get("evidence") or {}
        for kind in ("write_sites", "read_sites", "read_write_sites"):
            for site in sites.get(kind) or []:
                paragraph = str(site.get("paragraph") or "").strip().upper()
                if paragraph:
                    found.add(paragraph)
    return found


def check_literal_completeness(
    statements: List[Tuple[int, str, str]], literal_artifact: Any
) -> Dict[str, Any]:
    """Every literal MOVE in the source must appear in the literal artifact."""
    in_source: Dict[tuple, int] = {}
    for statement in statements:
        for match in MOVE_LITERAL_RE.finditer(statement.raw):
            literal = match.group("literal")
            if len(literal) >= 2 and literal[0] == literal[-1] and literal[0] in "'\"":
                literal = literal[1:-1]
            in_source[(match.group("target").upper(), literal)] = statement.line

    in_artifact = {
        (str(a.get("target_variable") or "").upper(), str(a.get("literal") or ""))
        for a in (literal_artifact.get("assignments") or [])
    }

    missing = [
        {"variable": v, "literal": lit, "line": in_source[(v, lit)]}
        for (v, lit) in sorted(set(in_source) - in_artifact)
    ]
    extra = [
        {"variable": v, "literal": lit}
        for (v, lit) in sorted(in_artifact - set(in_source))
    ]
    return {
        "check": "literal_assignments_match_source",
        "description": "Literal MOVEs found in the source appear in dataflow.literal_assignments",
        "source_count": len(in_source),
        "artifact_count": len(in_artifact),
        "missing_from_artifact": missing,
        "not_found_in_source": extra,
        "ok": not missing and not extra,
    }


def check_write_site_coverage(
    statements: List[Tuple[int, str, str]], evidence: Dict[str, Dict[str, Set[int]]]
) -> Dict[str, Any]:
    """A MOVE ... TO <var> line must be recorded as a write of <var>.

    This is the general form of the literal gap: a receiving field filed as a
    read rather than a write. Checking it here catches the misclassification
    for every variable, not only the ones that receive literals.
    """
    misfiled: List[Dict[str, Any]] = []
    for statement in statements:
        line_no, text = statement.line, statement.normalized
        for match in MOVE_ANY_RE.finditer(text):
            target = match.group("target").upper()
            record = evidence.get(target)
            if record is None:
                continue  # not in the inventory (e.g. filtered keyword); other checks cover this
            if line_no in record["write"]:
                continue
            misfiled.append(
                {
                    "variable": target,
                    "line": line_no,
                    "recorded_as_read": line_no in record["read"],
                    "statement": text[:120],
                }
            )
    return {
        "check": "move_targets_recorded_as_writes",
        "description": "Each MOVE ... TO <var> source line is a write site for <var>",
        "misfiled": misfiled,
        "ok": not misfiled,
    }


def check_cfg_covers_source_paragraphs(
    cfg: Any, rows: Iterable[Dict[str, Any]]
) -> Dict[str, Any]:
    """Every paragraph in the source must be a control-flow node.

    A paragraph the graph does not know cannot be counted, walked, or returned
    as the answer to a reverse-edge query, and its absence is invisible: the
    graph simply reports one fewer node than the program has.
    """
    nodes = {str(n).upper() for n in (cfg.get("nodes") or []) if n}
    declared = source_paragraphs(rows)
    return {
        "check": "cfg_covers_source_paragraphs",
        "description": "Every PROCEDURE DIVISION paragraph appears as a control-flow node",
        "source_paragraph_count": len(declared),
        "cfg_node_count": len(nodes),
        "missing_from_cfg": sorted(declared - nodes),
        "not_in_source": sorted(nodes - declared),
        "ok": not (declared - nodes) and not (nodes - declared),
    }


def check_reported_paragraph_count(
    comments: Any, rows: Iterable[Dict[str, Any]]
) -> Dict[str, Any]:
    """A reported paragraph count must match the number of paragraphs.

    Several builders detect paragraphs independently. When one of them drifts,
    the disagreement surfaces to the user as competing counts with no way to
    tell which is right, so the count is checked against the source map here.
    """
    declared = source_paragraphs(rows)
    reported = None
    if isinstance(comments, dict):
        metrics = comments.get("metrics")
        if isinstance(metrics, dict):
            reported = metrics.get("total_procedure_paragraphs")
    if not isinstance(reported, int):
        return {
            "check": "reported_paragraph_count_matches_source",
            "description": "program.comments paragraph count matches the source map",
            "reported": None,
            "ok": True,
            "note": "no count reported",
        }
    # The source map includes the implicit leading paragraph; a builder that
    # only counts explicit labels is short by exactly that one.
    return {
        "check": "reported_paragraph_count_matches_source",
        "description": "program.comments paragraph count matches the source map",
        "reported": reported,
        "source_paragraph_count": len(declared),
        "difference": reported - len(declared),
        "ok": reported in (len(declared), len(declared) - 1),
    }


def check_paragraphs_not_variables(
    cfg: Any, evidence: Dict[str, Dict[str, Set[int]]]
) -> Dict[str, Any]:
    """Paragraph names must not leak into the variable inventory.

    A flow target parsed as a data reference produces a variable that does not
    exist, which downstream reads as real evidence.
    """
    nodes = {str(n).upper() for n in (cfg.get("nodes") or []) if n}
    leaked = sorted(nodes & set(evidence))
    return {
        "check": "paragraph_names_absent_from_variables",
        "description": "Control-flow node names do not appear as variables",
        "leaked": leaked,
        "ok": not leaked,
    }


def check_site_paragraphs_known(cfg: Any, used_variables: Any) -> Dict[str, Any]:
    """Evidence sites must cite paragraphs the control-flow graph knows."""
    nodes = {str(n).upper() for n in (cfg.get("nodes") or []) if n}
    unknown = sorted(p for p in site_paragraphs(used_variables) if p not in nodes)
    return {
        "check": "evidence_paragraphs_exist_in_cfg",
        "description": "Every variable evidence site cites a known control-flow node",
        "unknown_paragraphs": unknown,
        "ok": not unknown,
    }


def check_literal_targets_known(
    literal_artifact: Any, evidence: Dict[str, Dict[str, Set[int]]]
) -> Dict[str, Any]:
    unknown = sorted(
        {
            str(a.get("target_variable") or "").upper()
            for a in (literal_artifact.get("assignments") or [])
        }
        - set(evidence)
    )
    return {
        "check": "literal_targets_exist_in_inventory",
        "description": "Literal assignment targets are present in dataflow.used_variables",
        "unknown_targets": unknown,
        "ok": not unknown,
    }


def build_report(artifacts_dir: Path, program: str) -> Dict[str, Any]:
    source_lines_path = artifacts_dir / "program.source_lines.jsonl"
    used_variables_path = artifacts_dir / "dataflow.used_variables.json"
    literals_path = artifacts_dir / "dataflow.literal_assignments.json"
    comments_path = artifacts_dir / "program.comments.json"
    cfg_path = artifacts_dir / "controlflow.cfg.json"

    missing_inputs = [
        str(p.name)
        for p in (source_lines_path, used_variables_path, literals_path, cfg_path)
        if not p.exists()
    ]
    if missing_inputs:
        return {
            "type": "quality.reconciliation_report",
            "program": program,
            "status": "skipped",
            "missing_inputs": missing_inputs,
            "checks": [],
        }

    rows = load_source_lines(source_lines_path)
    statements = procedure_statements(rows)
    used_variables = load_json(used_variables_path)
    literal_artifact = load_json(literals_path)
    cfg = load_json(cfg_path)
    comments = load_json(comments_path) if comments_path.exists() else None
    evidence = variable_evidence(used_variables)

    checks = [
        check_literal_completeness(statements, literal_artifact),
        check_cfg_covers_source_paragraphs(cfg, rows),
        check_reported_paragraph_count(comments, rows),
        check_write_site_coverage(statements, evidence),
        check_paragraphs_not_variables(cfg, evidence),
        check_site_paragraphs_known(cfg, used_variables),
        check_literal_targets_known(literal_artifact, evidence),
    ]

    failed = [c["check"] for c in checks if not c["ok"]]
    return {
        "type": "quality.reconciliation_report",
        "program": program,
        "status": "ok" if not failed else "discrepancies",
        "procedure_statements": len(statements),
        "variables": len(evidence),
        "failed_checks": failed,
        "checks": checks,
    }


def print_summary(report: Dict[str, Any]) -> None:
    program = report.get("program")
    if report.get("status") == "skipped":
        print(f"[SKIP] {program}: missing {', '.join(report.get('missing_inputs') or [])}")
        return
    print(f"=== reconciliation: {program} ({report['procedure_statements']} statements, "
          f"{report['variables']} variables)")
    for check in report["checks"]:
        mark = "ok  " if check["ok"] else "FAIL"
        print(f"  [{mark}] {check['check']}")
        if check["ok"]:
            continue
        for key, value in check.items():
            if key in {"check", "description", "ok"} or not isinstance(value, list):
                continue
            for item in value[:20]:
                print(f"         - {item}")
            if len(value) > 20:
                print(f"         ... +{len(value) - 20} more")
    print(f"  status: {report['status']}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Cross-check derived artifacts against the physical source map"
    )
    ap.add_argument("--artifacts-root", required=True, help="Program artifacts directory")
    ap.add_argument("--program", required=True)
    ap.add_argument("--output", help="Where to write the JSON report")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any invariant fails (for CI; the pipeline reports only)",
    )
    args = ap.parse_args()

    report = build_report(Path(args.artifacts_root), args.program)
    print_summary(report)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] Wrote reconciliation report to {out}")

    if args.strict and report.get("status") == "discrepancies":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
