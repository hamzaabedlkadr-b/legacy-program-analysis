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
    ap = argparse.ArgumentParser(description="Inspect condition quality in an enriched PDC graph")
    ap.add_argument("--input", default=str(DEFAULT_INPUT), help="Path to pdc_enriched.json")
    args = ap.parse_args()

    # Load the enriched graph
    data = load_json(Path(args.input))

    edges = data.get("edges")
    if not isinstance(edges, list):
        die("expected 'edges' to be a list in pdc_enriched.json")
    jumps = [e for e in edges if e.get("type") == "JUMP"]
    with_cond = [e for e in jumps if "condition" in e]

    print("=" * 80)
    print("ENRICHED GRAPH EVALUATION REPORT")
    print("=" * 80)
    print(f"\nTotal edges: {len(edges)}")
    print(f"JUMP edges: {len(jumps)}")
    print(f"JUMP edges with conditions: {len(with_cond)}")

    # Check for unbalanced parentheses
    unbalanced = []
    for e in with_cond:
        cond = e["condition"]
        op = cond.count("(")
        cp = cond.count(")")
        if op != cp:
            unbalanced.append((e, op, cp))

    print(f"\nUnbalanced conditions: {len(unbalanced)}")

    # Check for duplicate subconditions
    duplicates = []
    for e in with_cond:
        cond = e["condition"]
        # Check for obvious duplicates like "X = 'A' OR X = 'A'"
        parts = re.split(r"\s+OR\s+", cond, flags=re.I)
        seen = set()
        for part in parts:
            part_clean = re.sub(r"[()]", "", part).strip()
            if part_clean in seen:
                duplicates.append((e, part_clean))
                break
            seen.add(part_clean)

    print(f"Conditions with duplicates: {len(duplicates)}")

    # Count edge types
    edge_types = {}
    for e in edges:
        etype = e.get("type", "UNKNOWN")
        edge_types[etype] = edge_types.get(etype, 0) + 1

    print(f"\nEdge type distribution:")
    for etype, count in sorted(edge_types.items()):
        print(f"  {etype}: {count}")

    # Check metadata
    meta = data.get("meta", {})
    print(f"\nMetadata:")
    print(f"  Program ID: {meta.get('program_id', 'N/A')}")
    print(f"  PERFORM ranges detected: {len(meta.get('ranges_detected', []))}")

    # Detailed error report
    if unbalanced:
        print(f"\n{'=' * 80}")
        print("UNBALANCED CONDITIONS DETAIL:")
        print("=" * 80)
        for e, op, cp in unbalanced[:10]:
            diff = op - cp
            print(f"\n  From: {e['from']} -> To: {e['to']}")
            print(f"  Opening: {op}, Closing: {cp}, Difference: {diff}")
            cond = e["condition"]
            if len(cond) > 100:
                print(f"  Condition: {cond[:100]}...")
            else:
                print(f"  Condition: {cond}")

    if duplicates:
        print(f"\n{'=' * 80}")
        print("DUPLICATE CONDITIONS DETAIL:")
        print("=" * 80)
        for e, dup_part in duplicates[:5]:
            print(f"\n  From: {e['from']} -> To: {e['to']}")
            print(f"  Duplicate part: {dup_part[:60]}...")

    # Success rate
    total_conditions = len(with_cond)
    correct_conditions = total_conditions - len(unbalanced) - len(duplicates)
    success_rate = (correct_conditions / total_conditions * 100) if total_conditions > 0 else 0

    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print("=" * 80)
    print(f"Total conditions analyzed: {total_conditions}")
    print(f"Correct conditions: {correct_conditions} ({success_rate:.1f}%)")
    unbalanced_pct = (len(unbalanced) / total_conditions * 100) if total_conditions > 0 else 0
    duplicate_pct = (len(duplicates) / total_conditions * 100) if total_conditions > 0 else 0
    print(f"Unbalanced conditions: {len(unbalanced)} ({unbalanced_pct:.1f}%)")
    print(f"Conditions with duplicates: {len(duplicates)} ({duplicate_pct:.1f}%)")


if __name__ == "__main__":
    main()
