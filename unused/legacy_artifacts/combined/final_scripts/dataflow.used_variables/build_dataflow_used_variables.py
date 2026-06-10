#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Build dataflow.used_variables.json from pdc_var_index_used.json")
    ap.add_argument("--input", required=True, help="Path to pdc_var_index_used.json")
    ap.add_argument("--output", required=True, help="Output dataflow.used_variables.json path")
    args = ap.parse_args()

    vars_used = json.loads(Path(args.input).read_text(encoding="utf-8"))
    out = {
        "type": "dataflow.used_variables",
        "program": "PDCBVC",
        "variables": vars_used,
        "source": "pdc_var_index_used.json",
    }

    Path(args.output).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Wrote {args.output}")


if __name__ == "__main__":
    main()
