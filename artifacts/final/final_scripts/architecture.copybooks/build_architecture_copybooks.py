#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Extract architecture.copybooks from rag_documents.json")
    ap.add_argument("--input", required=True, help="Path to rag_documents.json")
    ap.add_argument("--program", required=True, help="Program name to extract")
    ap.add_argument("--output", required=True, help="Output architecture.copybooks.json path")
    args = ap.parse_args()

    docs = json.loads(Path(args.input).read_text(encoding="utf-8"))
    matches = [d for d in docs if d.get("type") == "architecture.copybooks" and d.get("program") == args.program]
    if not matches:
        raise SystemExit(f"architecture.copybooks not found for program: {args.program}")

    out = matches[0]
    Path(args.output).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Wrote {args.output}")


if __name__ == "__main__":
    main()
