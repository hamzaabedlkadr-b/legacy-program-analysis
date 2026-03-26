import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional


# ===============================
# Utilities
# ===============================

def load_json(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        die(f"input file not found: {path}")
    except json.JSONDecodeError as exc:
        die(f"invalid JSON in {path} (line {exc.lineno}, col {exc.colno})")
    except Exception as exc:
        die(f"failed to read {path}: {exc}")


def save_json(path: Path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        die(f"failed to write {path}: {exc}")


def die(msg: str, code: int = 1) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    raise SystemExit(code)


def clean_text(text: Optional[str]) -> Optional[str]:
    """
    Formatting cleanup ONLY.
    DO NOT rewrite logic (no IN[], no DeMorgan, etc).
    """
    if text is None:
        return None
    return " ".join(text.replace("\n", " ").split())


# ===============================
# Heuristic sets
# ===============================

# Variables that strongly suggest paging/counters/technical flow
TECH_VARS = {
    "WCTRIG", "WCTPAG", "MAX-RIGHE", "NPAG", "NPAGT", "RIGHE", "PAG"
}

# Variables that often represent business mode / operation selection
BUSINESS_MODE_VARS = {
    "TWCOB-FUNZIONE",
    "TWCOB-VARCONT-NUMFUNZ",
    "TWCOB-XCTL-PGM",
}

# UI key vars
UI_VARS = {"EIBAID"}
UI_TOKENS = {"DFHENTER", "DFHPF1", "DFHPF2", "DFHPF3", "DFHPF4", "DFHPF7", "DFHPF8", "DFHPF9"}


# ===============================
# Classification helpers
# ===============================

def classify_category(edge: Dict) -> str:
    tgt = (edge.get("to") or "").upper()
    etype = (edge.get("type") or "").upper()

    if "ABEND" in tgt:
        return "error"
    if "XCTL" in tgt:
        return "permission"
    if etype in ("CALL", "CALL_RANGE"):
        return "precondition"
    if tgt in ("RETURN", "EXIT"):
        return "validation"
    return "control"


def contains_any_token(haystack_upper: str, tokens: set) -> bool:
    return any(tok in haystack_upper for tok in tokens)


def classify_kind(category: str, condition: str) -> str:
    """
    kind is a higher-level semantic grouping.
    IMPORTANT: We may override 'permission' if the condition is purely technical (pagination)
    because otherwise it pollutes business rules.
    """
    cond_u = (condition or "").upper()

    # UI navigation logic
    if (contains_any_token(cond_u, UI_VARS) or contains_any_token(cond_u, UI_TOKENS)):
        return "ui"

    # If condition clearly references paging/counter vars => technical (even if XCTL)
    if contains_any_token(cond_u, TECH_VARS):
        return "technical"

    # Mode/operation selection (often business semantics but not necessarily permissions/errors)
    if contains_any_token(cond_u, BUSINESS_MODE_VARS):
        # If it was already business-critical (error/permission/precondition/validation), keep business
        if category in ("error", "permission", "precondition", "validation"):
            return "business"
        return "business_logic"

    # Phase/state routing
    if "TWCOB-FASE" in cond_u:
        return "state"

    # Default: if category is business-critical, mark business
    if category in ("error", "permission", "precondition", "validation"):
        return "business"

    return "control"


def classify_severity(category: str) -> str:
    return {
        "error": "fatal",
        "permission": "block",
        "precondition": "guard",
        "validation": "reject",
        "control": "neutral",
    }.get(category, "neutral")


# ===============================
# Flags / QA
# ===============================

_NOT_A_OR_B = re.compile(r"\(\s*NOT\s*\(.+?\)\s+OR\s+\(.+?\)\s*\)", re.IGNORECASE)

def detect_flags(condition: str) -> List[str]:
    """
    Flags to help you audit upstream condition synthesis.
    Does NOT alter logic.
    """
    flags = []
    c = condition or ""

    # Pattern: (NOT(A) OR B) — often means "else branch" got encoded weirdly
    if _NOT_A_OR_B.search(c):
        flags.append("condition_maybe_inverted_notA_or_B")

    # Pattern: self-contradicting-looking forms can be added later
    return flags


# ===============================
# Core extraction
# ===============================

def extract_rules(enriched: Dict, program_name: str) -> Dict:
    rules = []
    counter = 1

    edges = enriched.get("edges", [])
    if not isinstance(edges, list):
        die("expected enriched['edges'] to be a list of edges")

    for edge in edges:
        condition = edge.get("condition")
        if not condition:
            continue

        category = classify_category(edge)
        severity = classify_severity(category)

        # keep original condition text (only whitespace cleanup)
        condition_clean = clean_text(condition)

        kind = classify_kind(category, condition_clean)

        # Drop purely technical rules from the rules file (as requested earlier)
        # This prevents WCTPAG/NPAGT/XCTL cases from polluting RAG.
        if kind == "technical":
            continue

        flags = detect_flags(condition_clean)

        rule = {
            "id": f"BR-{counter:03d}",
            "program": program_name,
            "scope": edge.get("from"),
            "category": category,
            "kind": kind,
            "severity": severity,
            "condition": condition_clean,
            "action": f"{edge.get('type')} → {edge.get('to')}",
            "flags": flags,
            "evidence": {
                "from": edge.get("from"),
                "to": edge.get("to"),
                "type": edge.get("type"),
                "raw_evidence": edge.get("evidence"),
            },
        }

        rules.append(rule)
        counter += 1

    return {"program": program_name, "rules": rules}


# ===============================
# Main
# ===============================

def main():
    import argparse

    ap = argparse.ArgumentParser(description="Extract semantic rules from pdc_enriched.json")
    ap.add_argument("--input", default="pdc_enriched.json", help="Path to pdc_enriched.json")
    ap.add_argument("--output", default="pdc_rules.json", help="Output pdc_rules.json path")
    ap.add_argument("--program", default=None, help="Override program name (optional)")
    args = ap.parse_args()

    enriched_path = Path(args.input)
    output_path = Path(args.output)

    enriched = load_json(enriched_path)
    if not isinstance(enriched, dict):
        raise ValueError("Expected pdc_enriched.json to be a JSON object (dict)")

    program_name = args.program or (enriched.get("graph") or {}).get("name", "UNKNOWN")

    rules_doc = extract_rules(enriched, program_name)
    save_json(output_path, rules_doc)

    print(f"[OK] Extracted {len(rules_doc['rules'])} semantic rules → {output_path}")


if __name__ == "__main__":
    main()

