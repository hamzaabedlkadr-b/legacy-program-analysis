import argparse
import json
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / "artifacts" / "intermediate" / "pdc_enriched.json"


def die(msg: str, code: int = 1) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    raise SystemExit(code)


def load_json(path: Path):
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        die(f"input file not found: {path}")
    except json.JSONDecodeError as exc:
        die(f"invalid JSON in {path} (line {exc.lineno}, col {exc.colno})")
    except Exception as exc:
        die(f"failed to read {path}: {exc}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Check for structural and duplicate condition issues")
    ap.add_argument("--input", default=str(DEFAULT_INPUT), help="Path to pdc_enriched.json")
    args = ap.parse_args()

    # Load the enriched graph
    data = load_json(Path(args.input))

    edges_raw = data.get("edges")
    if not isinstance(edges_raw, list):
        die("expected 'edges' to be a list in pdc_enriched.json")
    edges = [e for e in edges_raw if e.get("type") == "JUMP" and "condition" in e]

    print("=" * 80)
    print("CHECKING FOR LOGICAL ERRORS vs DUPLICATES")
    print("=" * 80)

    # Check 1: Unbalanced parentheses (count)
    unbalanced_count = []
    for e in edges:
        cond = e["condition"]
        op = cond.count("(")
        cp = cond.count(")")
        if op != cp:
            unbalanced_count.append((e, op, cp))

    print(f"\n1. Unbalanced by COUNT: {len(unbalanced_count)}")
    if unbalanced_count:
        for e, op, cp in unbalanced_count[:3]:
            print(f"   {e['from']} -> {e['to']}: {op} open, {cp} close")

    # Check 2: Structural issues (excessive consecutive parentheses)
    structural_issues = []
    for e in edges:
        cond = e["condition"]
        # Check for patterns like ))))) or (((((
        if re.search(r"\){4,}", cond) or re.search(r"\({4,}", cond):
            structural_issues.append(e)

    print(f"\n2. Structural issues (excessive consecutive parens): {len(structural_issues)}")
    if structural_issues:
        for e in structural_issues[:5]:
            # Find the problematic part
            cond = e["condition"]
            match = re.search(r"\){4,}|\({4,}", cond)
            if match:
                start = max(0, match.start() - 30)
                end = min(len(cond), match.end() + 30)
                print(f"   {e['from']} -> {e['to']}:")
                print(f"      ...{cond[start:end]}...")

    # Check 3: Duplicates (same condition repeated)
    duplicates = []
    for e in edges:
        cond = e["condition"]
        # Split by OR and check for duplicates
        parts = re.split(r"\s+OR\s+", cond, flags=re.I)
        # Normalize each part (remove parens, normalize spacing)
        normalized_parts = []
        for part in parts:
            norm = re.sub(r"[()]", "", part).strip()
            norm = re.sub(r"\s+", " ", norm)
            normalized_parts.append(norm)

        # Check for duplicates
        seen = set()
        for norm in normalized_parts:
            if norm in seen and norm:  # non-empty duplicate
                duplicates.append((e, norm))
                break
            seen.add(norm)

    print(f"\n3. Duplicate conditions: {len(duplicates)}")
    if duplicates:
        for e, dup in duplicates[:5]:
            print(f"   {e['from']} -> {e['to']}: duplicate '{dup[:50]}...'")

    # Check 4: Malformed structure (parens in wrong places)
    malformed = []
    for e in edges:
        cond = e["condition"]
        # Check for patterns like: (X = 'A'))))))) - closing parens after a complete condition
        if re.search(r"=\s*'[^']+'\s*\){3,}", cond):
            malformed.append(e)
        # Check for: (((((X = 'A') - excessive opening before
        if re.search(r"\({3,}[A-Z0-9\-]+\s*=", cond):
            malformed.append(e)

    print(f"\n4. Malformed structure: {len(malformed)}")
    if malformed:
        for e in malformed[:5]:
            cond = e["condition"]
            print(f"   {e['from']} -> {e['to']}: {cond[:80]}...")

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print("=" * 80)
    total = len(edges)
    logical_errors = len(unbalanced_count) + len(structural_issues) + len(malformed)
    duplicate_only = len(duplicates) - len([d for d in duplicates if any(d[0] == m for m in structural_issues + malformed)])

    print(f"Total conditions: {total}")
    print(f"Logical/Structural errors: {logical_errors}")
    print(f"Pure duplicates (no structural issues): {duplicate_only}")
    print(f"Correct conditions: {total - logical_errors - duplicate_only}")

    if logical_errors > 0:
        print(f"\nWARNING: You have LOGICAL ERRORS, not just duplicates!")
        print("   These conditions are malformed and may not work correctly.")
    else:
        print(f"\nOK: Only duplicates found - conditions are logically correct!")


if __name__ == "__main__":
    main()
