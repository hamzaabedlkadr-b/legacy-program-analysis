#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from pathlib import Path


SAFE_RE = re.compile(r"[^A-Z0-9-]+")


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


def main():
    ap = argparse.ArgumentParser(description="Build business_rule.*.json from pdc_rules.json")
    ap.add_argument("--input", required=True, help="Path to pdc_rules.json")
    ap.add_argument("--program", required=True, help="Program name to extract")
    ap.add_argument("--out-dir", required=True, help="Output directory for business_rule.*.json files")
    args = ap.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    rules = data.get("rules") or []

    program = args.program.upper()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

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
            },
        }

        out_path = out_dir / f"business_rule.{safe_name(rule_id)}.json"
        out_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        wrote += 1

    print(f"[OK] Wrote {wrote} business_rule.*.json files to {out_dir}")


if __name__ == "__main__":
    main()
