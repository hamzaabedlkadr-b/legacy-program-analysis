import json
import sys
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / "artifacts" / "intermediate" / "pdc_rules.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "artifacts" / "intermediate" / "rag_documents.json"


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


# ===============================
# Text templates (NO logic rewriting)
# ===============================

def build_embedding_text(rule: Dict) -> str:
    """
    Create a natural-language description for embedding.
    DO NOT rewrite or normalize conditions.
    """
    category = rule["category"]
    scope = rule["scope"]
    condition = rule["condition"]
    action = rule["action"]

    if category == "error":
        return (
            f"The program terminates with an error when the condition "
            f"'{condition}' is met in paragraph {scope}."
        )

    if category == "permission":
        return (
            f"The operation is blocked when the condition '{condition}' "
            f"is satisfied in paragraph {scope}."
        )

    if category == "precondition":
        return (
            f"The operation is allowed only when the condition '{condition}' "
            f"is true in paragraph {scope}."
        )

    if category == "validation":
        return (
            f"The program validates that '{condition}' holds before continuing "
            f"in paragraph {scope}."
        )

    # fallback (should rarely be used for business rules)
    return (
        f"A business rule applies when the condition '{condition}' "
        f"is evaluated in paragraph {scope}."
    )


# ===============================
# Core generation
# ===============================

def generate_rag_documents(pdc_rules: Dict) -> List[Dict]:
    program = pdc_rules.get("program", "UNKNOWN")
    rules = pdc_rules.get("rules", [])

    rag_docs = []

    for rule in rules:
        # STRICT FILTER: only embed business rules
        if rule.get("kind") != "business":
            continue

        rag_doc = {
            "id": f"RAG-{rule['id']}",
            "program": program,
            "type": "business_rule",
            "source_rule_id": rule["id"],
            "embedding_text": build_embedding_text(rule),
            "content": {
                "category": rule["category"],
                "severity": rule["severity"],
                "condition": rule["condition"],
                "action": rule["action"],
                "scope": rule["scope"]
            },
            "evidence": rule.get("evidence", {}),
            "flags": rule.get("flags", [])
        }

        rag_docs.append(rag_doc)

    return rag_docs


# ===============================
# Main
# ===============================

def main():
    import argparse

    ap = argparse.ArgumentParser(description="Generate rag_documents.json from pdc_rules.json")
    ap.add_argument("--input", default=str(DEFAULT_INPUT), help="Path to pdc_rules.json")
    ap.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output rag_documents.json path")
    args = ap.parse_args()

    rules_path = Path(args.input)
    output_path = Path(args.output)

    pdc_rules = load_json(rules_path)

    rag_docs = generate_rag_documents(pdc_rules)

    save_json(output_path, rag_docs)

    print(f"[OK] Generated {len(rag_docs)} RAG documents → {output_path}")


if __name__ == "__main__":
    main()

