#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Extract architecture.sqlinclude.* from rag_documents.json")
    ap.add_argument("--input", required=True, help="Path to rag_documents.json")
    ap.add_argument("--program", required=True, help="Program name to extract")
    ap.add_argument("--out-dir", required=True, help="Output directory for architecture.sqlinclude.*.json files")
    args = ap.parse_args()

    docs = json.loads(Path(args.input).read_text(encoding="utf-8"))
    incs = [d for d in docs if d.get("type") == "architecture.sqlinclude" and d.get("program") == args.program]
    if not incs:
        raise SystemExit(f"architecture.sqlinclude not found for program: {args.program}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for d in incs:
        include = (d.get("content") or {}).get("include") or d.get("title")
        safe_inc = str(include).replace(" ", "_").replace("/", "_")
        fname = f"architecture.sqlinclude.{safe_inc}.json"
        out_path = out_dir / fname
        out_path.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[OK] Wrote {len(incs)} architecture.sqlinclude.*.json files to {out_dir}")


if __name__ == "__main__":
    main()
