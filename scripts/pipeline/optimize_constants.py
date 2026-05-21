#!/usr/bin/env python3
"""Conservative constant folding/propagation for generated COBOL artifacts.

This pass is designed to reduce noisy analysis artifacts before RAG indexing
without changing source COBOL. It works on generated JSON only.

Supported optimizations:
- fold simple literal comparisons in CFG edge conditions;
- expand and deduplicate COBOL shorthand conditions such as X = 'A' OR 'B';
- simplify top-level TRUE/FALSE boolean terms;
- locally propagate literal MOVE values into later IF/control evidence within
  the same paragraph;
- deduplicate repeated evidence sites after normalization.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any


MOVE_LITERAL_RE = re.compile(
    r"\bMOVE\s+(?P<literal>'[^']*'|\"[^\"]*\"|[+-]?\d+(?:\.\d+)?|ZEROES?|SPACES?)\s+TO\s+(?P<target>[A-Z0-9-]+)\b",
    re.IGNORECASE,
)
IDENT_RE = re.compile(r"\b[A-Z][A-Z0-9-]*\b")
LITERAL_RE = r"(?:'[^']*'|\"[^\"]*\"|[+-]?\d+(?:\.\d+)?|ZEROES?|SPACES?)"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def strip_outer_parens(text: str) -> str:
    text = text.strip()
    while text.startswith("(") and text.endswith(")") and wraps_entire_expression(text):
        text = text[1:-1].strip()
    return text


def wraps_entire_expression(text: str) -> bool:
    depth = 0
    in_quote: str | None = None
    for index, char in enumerate(text):
        if in_quote:
            if char == in_quote:
                in_quote = None
            continue
        if char in {"'", '"'}:
            in_quote = char
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0 and index != len(text) - 1:
                return False
    return depth == 0


def split_top_level(expr: str, operator: str) -> list[str]:
    expr = expr.strip()
    parts: list[str] = []
    depth = 0
    in_quote: str | None = None
    start = 0
    pattern = f" {operator} "
    upper = expr.upper()
    index = 0
    while index < len(expr):
        char = expr[index]
        if in_quote:
            if char == in_quote:
                in_quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            in_quote = char
            index += 1
            continue
        if char == "(":
            depth += 1
            index += 1
            continue
        if char == ")":
            depth = max(0, depth - 1)
            index += 1
            continue
        if depth == 0 and upper.startswith(pattern, index):
            parts.append(expr[start:index].strip())
            index += len(pattern)
            start = index
            continue
        index += 1
    if parts:
        parts.append(expr[start:].strip())
    return parts


def normalize_literal(raw: str) -> str:
    raw = raw.strip()
    upper = raw.upper()
    if upper in {"ZERO", "ZEROS", "ZEROES"}:
        return "0"
    if upper in {"SPACE", "SPACES"}:
        return ""
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
        return raw[1:-1]
    return raw


def canonical_literal(raw: str) -> str:
    raw = raw.strip()
    if re.fullmatch(r"[+-]?\d+(?:\.\d+)?", raw):
        return raw
    upper = raw.upper()
    if upper in {"ZERO", "ZEROS", "ZEROES"}:
        return "0"
    if upper in {"SPACE", "SPACES"}:
        return "''"
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
        return "'" + raw[1:-1] + "'"
    return raw


def literal_value(raw: str) -> tuple[str, Any]:
    value = normalize_literal(raw)
    if re.fullmatch(r"[+-]?\d+(?:\.\d+)?", value):
        return "number", float(value) if "." in value else int(value)
    return "string", value


def evaluate_literal_comparison(match: re.Match[str]) -> str:
    left = match.group("left")
    op = normalize_spaces(match.group("op")).upper()
    right = match.group("right")
    left_kind, left_value = literal_value(left)
    right_kind, right_value = literal_value(right)
    if left_kind != right_kind and op not in {"=", "EQUAL", "EQUALS", "NOT =", "NOT EQUAL", "NOT EQUALS"}:
        return match.group(0)
    if op in {"=", "EQUAL", "EQUALS"}:
        return "TRUE" if left_value == right_value else "FALSE"
    if op in {"NOT =", "NOT EQUAL", "NOT EQUALS"}:
        return "TRUE" if left_value != right_value else "FALSE"
    if op in {">", "GREATER", "GREATER THAN"}:
        return "TRUE" if left_value > right_value else "FALSE"
    if op in {"<", "LESS", "LESS THAN"}:
        return "TRUE" if left_value < right_value else "FALSE"
    return match.group(0)


def expand_cobol_or_shorthand(expr: str) -> str:
    """Expand X = 'A' OR 'B' into X = 'A' OR X = 'B'."""
    token = LITERAL_RE
    pattern = re.compile(
        rf"(?P<var>\b[A-Z][A-Z0-9-]*\b)\s*(?P<op>=|NOT\s*=|EQUALS?|NOT\s+EQUALS?)\s*(?P<first>{token})(?P<rest>(?:\s+OR\s+{token})+)",
        re.IGNORECASE,
    )

    def repl(match: re.Match[str]) -> str:
        var = match.group("var")
        op = normalize_spaces(match.group("op"))
        values = [match.group("first")]
        values.extend(re.findall(token, match.group("rest"), flags=re.IGNORECASE))
        return " OR ".join(f"{var} {op} {value}" for value in values)

    previous = None
    current = expr
    while current != previous:
        previous = current
        current = pattern.sub(repl, current)
    return current


def dedupe_terms(parts: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for part in parts:
        clean = strip_outer_parens(normalize_spaces(part))
        key = re.sub(r"\s+", "", clean.upper())
        if key in seen:
            continue
        seen.add(key)
        out.append(clean)
    return out


def simplify_boolean(expr: str) -> str:
    expr = strip_outer_parens(normalize_spaces(expr))
    or_parts = split_top_level(expr, "OR")
    if or_parts:
        simplified = [simplify_boolean(part) for part in or_parts]
        if any(part == "TRUE" for part in simplified):
            return "TRUE"
        simplified = [part for part in simplified if part != "FALSE"]
        simplified = dedupe_terms(simplified)
        if not simplified:
            return "FALSE"
        if len(simplified) == 1:
            return simplified[0]
        return " OR ".join(f"({part})" if " AND " in part.upper() else part for part in simplified)

    and_parts = split_top_level(expr, "AND")
    if and_parts:
        simplified = [simplify_boolean(part) for part in and_parts]
        if any(part == "FALSE" for part in simplified):
            return "FALSE"
        simplified = [part for part in simplified if part != "TRUE"]
        simplified = dedupe_terms(simplified)
        if not simplified:
            return "TRUE"
        if len(simplified) == 1:
            return simplified[0]
        return " AND ".join(f"({part})" if " OR " in part.upper() else part for part in simplified)

    return expr


def optimize_condition(expr: str, constants: dict[str, str] | None = None) -> str:
    if not expr:
        return expr
    constants = constants or {}
    result = normalize_spaces(expr)
    result = expand_cobol_or_shorthand(result)
    for variable, literal in sorted(constants.items(), key=lambda item: len(item[0]), reverse=True):
        result = re.sub(rf"\b{re.escape(variable)}\b", canonical_literal(literal), result, flags=re.IGNORECASE)

    literal_cmp = re.compile(
        rf"(?P<left>{LITERAL_RE})\s*(?P<op>NOT\s*=|NOT\s+EQUALS?|=|EQUALS?|GREATER\s+THAN|GREATER|LESS\s+THAN|LESS|>|<)\s*(?P<right>{LITERAL_RE})",
        re.IGNORECASE,
    )
    previous = None
    while result != previous:
        previous = result
        result = literal_cmp.sub(evaluate_literal_comparison, result)
        result = simplify_boolean(result)
    return normalize_spaces(result)


def site_line(site: dict[str, Any]) -> int:
    try:
        return int(site.get("line_start") or site.get("line") or 0)
    except Exception:
        return 0


def parse_literal_write(statement: str, target: str) -> str | None:
    match = MOVE_LITERAL_RE.search(statement or "")
    if not match:
        return None
    if match.group("target").upper() != target.upper():
        return None
    return match.group("literal")


def local_constants_for_site(variable: dict[str, Any], site: dict[str, Any]) -> dict[str, str]:
    variable_name = str(variable.get("variable") or "").upper()
    paragraph = str(site.get("paragraph") or "")
    line = site_line(site)
    if not variable_name or not paragraph or line <= 0:
        return {}
    writes = ((variable.get("evidence") or {}).get("write_sites") or [])
    candidates: list[tuple[int, str]] = []
    for write in writes:
        if str(write.get("paragraph") or "") != paragraph:
            continue
        write_line = site_line(write)
        if write_line <= 0 or write_line > line:
            continue
        literal = parse_literal_write(str(write.get("statement") or ""), variable_name)
        if literal is not None:
            candidates.append((write_line, literal))
    if not candidates:
        return {}
    candidates.sort()
    return {variable_name: candidates[-1][1]}


def optimize_statement(statement: str, constants: dict[str, str]) -> str:
    text = normalize_spaces(statement)
    if not text:
        return text
    upper = text.upper()
    if upper.startswith("IF "):
        condition = re.sub(r"^IF\s+", "", text, flags=re.IGNORECASE)
        condition = re.sub(r"\s+THEN\.?$", "", condition, flags=re.IGNORECASE).strip()
        return "IF " + optimize_condition(condition, constants)
    return optimize_condition(text, constants) if any(op in upper for op in (" AND ", " OR ", " = ", " NOT ")) else text


def dedupe_sites(sites: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    seen: set[tuple[str, int, str]] = set()
    out: list[dict[str, Any]] = []
    removed = 0
    for site in sites:
        statement = normalize_spaces(str(site.get("statement") or ""))
        key = (str(site.get("paragraph") or ""), site_line(site), re.sub(r"\s+", "", statement.upper()))
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        out.append(site)
    return out, removed


def optimize_cfg(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, int]]:
    out = copy.deepcopy(data)
    stats = {
        "conditions_seen": 0,
        "conditions_changed": 0,
        "conditions_folded_true": 0,
        "conditions_folded_false": 0,
    }
    for edge in out.get("edges") or []:
        condition = edge.get("condition")
        if not isinstance(condition, str) or not condition.strip():
            continue
        stats["conditions_seen"] += 1
        optimized = optimize_condition(condition)
        if optimized != normalize_spaces(condition):
            edge["condition"] = optimized
            stats["conditions_changed"] += 1
        if optimized == "TRUE":
            stats["conditions_folded_true"] += 1
        elif optimized == "FALSE":
            stats["conditions_folded_false"] += 1
    meta = out.setdefault("meta", {})
    if isinstance(meta, dict):
        meta.setdefault("optimizations", {})["constant_folding"] = stats
    return out, stats


def optimize_variables(data: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    out = copy.deepcopy(data)
    stats = {
        "variables_seen": len(out),
        "sites_changed": 0,
        "duplicate_sites_removed": 0,
    }
    for variable in out:
        evidence = variable.get("evidence") or {}
        for bucket in ("read_sites", "control_sites"):
            sites = evidence.get(bucket) or []
            for site in sites:
                statement = str(site.get("statement") or "")
                constants = local_constants_for_site(variable, site)
                optimized = optimize_statement(statement, constants)
                if optimized and optimized != normalize_spaces(statement):
                    site["statement"] = optimized
                    stats["sites_changed"] += 1
            deduped, removed = dedupe_sites(sites)
            evidence[bucket] = deduped
            stats["duplicate_sites_removed"] += removed
        variable["evidence"] = evidence
    return out, stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cfg-in", type=Path, help="Input controlflow.cfg.json")
    parser.add_argument("--cfg-out", type=Path, help="Output optimized controlflow.cfg.json")
    parser.add_argument("--vars-in", type=Path, help="Input pdc_var_index_used.json")
    parser.add_argument("--vars-out", type=Path, help="Output optimized pdc_var_index_used.json")
    parser.add_argument("--report", type=Path, required=True, help="Optimization summary JSON path")
    args = parser.parse_args()

    report: dict[str, Any] = {"type": "optimization.constants", "stages": {}}

    if args.cfg_in:
        if not args.cfg_out:
            raise SystemExit("--cfg-out is required with --cfg-in")
        cfg, cfg_stats = optimize_cfg(load_json(args.cfg_in))
        save_json(args.cfg_out, cfg)
        report["stages"]["cfg"] = cfg_stats

    if args.vars_in:
        if not args.vars_out:
            raise SystemExit("--vars-out is required with --vars-in")
        variables, vars_stats = optimize_variables(load_json(args.vars_in))
        save_json(args.vars_out, variables)
        report["stages"]["variables"] = vars_stats

    save_json(args.report, report)
    print(f"[OK] Wrote optimization report to {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
