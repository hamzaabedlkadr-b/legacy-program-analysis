#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Extract architecture.db2_table.* from rag_documents.json")
    ap.add_argument("--input", required=True, help="Path to rag_documents.json")
    ap.add_argument("--program", required=True, help="Program name to extract")
    ap.add_argument("--out-dir", required=True, help="Output directory for architecture.db2_table.*.json files")
    args = ap.parse_args()

    docs = json.loads(Path(args.input).read_text(encoding="utf-8"))
    tables = [d for d in docs if d.get("type") == "architecture.db2_table" and d.get("program") == args.program]
    if not tables:
        raise SystemExit(f"architecture.db2_table not found for program: {args.program}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for d in tables:
        content = d.get("content") or {}
        table = content.get("table") or "TABLE"
        stmt = content.get("stmt_type") or "statement"
        safe_table = str(table).replace(" ", "_").replace("/", "_")
        safe_stmt = str(stmt).replace(" ", "_").replace("/", "_")
        fname = f"architecture.db2_table.{safe_table}.{safe_stmt}.json"
        out_path = out_dir / fname
        out_path.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[OK] Wrote {len(tables)} architecture.db2_table.*.json files to {out_dir}")


if __name__ == "__main__":
    main()
