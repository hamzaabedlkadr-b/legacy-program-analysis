#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


SAFE_RE = re.compile(r"[^A-Z0-9-]+")
PARAGRAPH_RE = re.compile(r"^([A-Z0-9][A-Z0-9-]*)\.\s*$", re.IGNORECASE)
NON_PARAGRAPHS = {"END-EXEC", "END-IF", "EJECT", "EXIT", "SKIP1", "SKIP2", "SKIP3"}


def make_id(text: str) -> str:
    return hashlib.blake2b(text.encode("utf-8"), digest_size=8).hexdigest()


def safe_name(text: str) -> str:
    t = (text or "").upper()
    t = SAFE_RE.sub("_", t).strip("_")
    return t or "RULE"


def normalize_action(action: str) -> str:
    if not action:
        return ""
    # Normalize arrow encodings to ASCII for embedding text
    return action.replace("â†’", "->").replace("→", "->")


def fixed_code(raw: str) -> str:
    padded = raw.rstrip("\n") + " " * max(0, 80 - len(raw.rstrip("\n")))
    if padded[6] in {"*", "/", "D", "d"}:
        return ""
    return padded[7:72].rstrip()


def normalize_cobol(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().upper().rstrip(".")


def index_source(path: Path, program: str) -> dict[str, list[tuple[int, str]]]:
    paragraphs: dict[str, list[tuple[int, str]]] = {}
    paragraph = ""
    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
    ):
        code = fixed_code(raw)
        if not code:
            continue
        if code.upper().startswith("PROCEDURE DIVISION"):
            paragraph = program.upper()
            paragraphs.setdefault(paragraph, [])
        match = PARAGRAPH_RE.fullmatch(code)
        if match and match.group(1).upper() not in NON_PARAGRAPHS:
            paragraph = match.group(1).upper()
            paragraphs.setdefault(paragraph, [])
        if paragraph:
            paragraphs.setdefault(paragraph, []).append((line_number, code.strip()))
    return paragraphs


def locate_rule(
    rule: dict,
    source_index: dict[str, list[tuple[int, str]]],
    source_file: str,
) -> dict[str, object] | None:
    scope = str(rule.get("scope") or "").upper()
    evidence = rule.get("evidence") or {}
    raw_evidence = str(evidence.get("raw_evidence") or "")
    target = normalize_cobol(raw_evidence)
    lines = source_index.get(scope, [])
    if not target or not lines:
        return None

    identifiers = set(re.findall(r"\b[A-Z][A-Z0-9-]*\b", str(rule.get("condition") or "").upper()))
    identifiers.difference_update({"AND", "OR", "NOT", "EQUAL", "TRUE", "FALSE"})
    candidates: list[tuple[int, int, int]] = []
    for index, (line_start, _code) in enumerate(lines):
        statement_parts: list[str] = []
        matched_end: int | None = None
        for offset in range(0, min(6, len(lines) - index)):
            line_end, code = lines[index + offset]
            statement_parts.append(code)
            if target in normalize_cobol(" ".join(statement_parts)):
                matched_end = line_end
                break
        if matched_end is None:
            continue
        context_start = max(0, index - 10)
        context = " ".join(code for _line, code in lines[context_start : index + 1]).upper()
        score = sum(1 for identifier in identifiers if identifier in context)
        candidates.append((score, line_start, matched_end))

    if not candidates:
        return None
    _score, line_start, line_end = max(
        candidates,
        key=lambda item: (item[0], -(item[2] - item[1]), item[1]),
    )
    return {
        "source_file": source_file,
        "line_start": line_start,
        "line_end": line_end,
    }


def main():
    ap = argparse.ArgumentParser(description="Build business_rule.*.json from pdc_rules.json")
    ap.add_argument("--input", required=True, help="Path to pdc_rules.json")
    ap.add_argument("--program", required=True, help="Program name to extract")
    ap.add_argument("--out-dir", required=True, help="Output directory for business_rule.*.json files")
    ap.add_argument("--cobol", type=Path, help="Optional COBOL source used to add physical source locations")
    args = ap.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    rules = data.get("rules") or []

    program = args.program.upper()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    source_index = index_source(args.cobol, program) if args.cobol and args.cobol.is_file() else {}

    has_program_match = any(
        str(r.get("program", "")).upper() == program or str(r.get("scope", "")).upper() == program
        for r in rules
    )

    wrote = 0
    for r in rules:
        rule_program = str(r.get("program", "")).upper()
        rule_scope = str(r.get("scope", "")).upper()
        # If any rule matches the requested program, treat the whole file as that program.
        # Otherwise, filter by explicit program/scope match.
        if not has_program_match and rule_program and rule_program != program and rule_scope != program:
            continue

        rule_id = r.get("id") or f"BR-{wrote + 1:03d}"
        scope = r.get("scope") or program
        category = r.get("category") or "unknown"
        kind = r.get("kind") or "unknown"
        severity = r.get("severity") or "unknown"
        condition = r.get("condition") or ""
        action = r.get("action") or ""
        flags = r.get("flags") or []

        # Normalize embedded program field for consistency
        content_rule = dict(r)
        content_rule["program"] = program
        if "action" in content_rule and isinstance(content_rule["action"], str):
            content_rule["action"] = normalize_action(content_rule["action"])
        location = locate_rule(r, source_index, args.cobol.name) if args.cobol else None
        if location:
            content_rule.setdefault("evidence", {}).update(location)

        embedding_text = (
            f"{program} business rule {rule_id} in scope {scope}. "
            f"If {condition} then {normalize_action(action)}. "
            f"Category={category}. Kind={kind}. Severity={severity}."
        )

        doc = {
            "id": make_id(f"{program}|{rule_id}|{scope}"),
            "type": "business_rule",
            "program": program,
            "title": f"{program} rule {rule_id}",
            "embedding_text": embedding_text,
            "content": content_rule,
            "meta": {
                "source": "pdc_rules.json",
                "scope": scope,
                "category": category,
                "kind": kind,
                "severity": severity,
                "flags_count": len(flags),
                "source_file": args.cobol.name if args.cobol else None,
            },
        }

        out_path = out_dir / f"business_rule.{safe_name(rule_id)}.json"
        out_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        wrote += 1

    print(f"[OK] Wrote {wrote} business_rule.*.json files to {out_dir}")


if __name__ == "__main__":
    main()
