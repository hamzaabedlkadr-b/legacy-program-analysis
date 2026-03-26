#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Build controlflow.cfg.json from pdc_enriched.json")
    ap.add_argument("--input", required=True, help="Path to pdc_enriched.json")
    ap.add_argument("--output", required=True, help="Output controlflow.cfg.json path")
    args = ap.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    out = {
        "type": "controlflow.cfg",
        "program": (data.get("meta") or {}).get("program_id") or (data.get("graph") or {}).get("name"),
        "graph": data.get("graph"),
        "nodes": data.get("nodes"),
        "edges": data.get("edges"),
        "meta": data.get("meta"),
        "source": "pdc_enriched.json",
    }

    Path(args.output).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Wrote {args.output}")


if __name__ == "__main__":
    main()
