#!/usr/bin/env python3
"""
filter_used_variables.py

Layer 2 — Program-Usage View

Keeps only variables that are actually used in the PROCEDURE DIVISION:
- read_sites != empty
- OR write_sites != empty
- OR control_sites != empty

Removes:
- unused COPYBOOK fields
- dead WORKING-STORAGE fields
- unused COMMAREA fields

Input:
- Full variable index JSON (from improve_var_index_v2.py)

Output:
- Reduced variable index JSON (program-usage view)

Usage:
  python filter_used_variables.py --in pdc_var_index_full.json --out pdc_var_index_used.json
"""

import argparse
import json
import sys
from pathlib import Path


def die(msg: str, code: int = 1) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    raise SystemExit(code)


def read_json(path: Path, label: str):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        die(f"{label} file not found: {path}")
    except json.JSONDecodeError as exc:
        die(f"invalid JSON in {path} (line {exc.lineno}, col {exc.colno})")
    except Exception as exc:
        die(f"failed to read {path}: {exc}")


def is_used(var: dict) -> bool:
    evidence = var.get("evidence", {})
    return (
        bool(evidence.get("read_sites"))
        or bool(evidence.get("write_sites"))
        or bool(evidence.get("control_sites"))
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="Input full var index JSON")
    ap.add_argument("--out", required=True, help="Output filtered var index JSON")
    args = ap.parse_args()

    in_path = Path(args.inp)
    out_path = Path(args.out)

    data = read_json(in_path, "input")

    total = len(data)
    used_vars = [v for v in data if is_used(v)]
    kept = len(used_vars)

    try:
        out_path.write_text(
            json.dumps(used_vars, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as exc:
        die(f"failed to write {out_path}: {exc}")

    print(f"[OK] Input variables : {total}")
    print(f"[OK] Used variables  : {kept}")
    print(f"[OK] Removed unused  : {total - kept}")
    print(f"[OK] Output written  : {out_path}")


if __name__ == "__main__":
    main()
