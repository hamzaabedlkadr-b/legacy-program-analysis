#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Extract architecture.call.* from rag_documents.json")
    ap.add_argument("--input", required=True, help="Path to rag_documents.json")
    ap.add_argument("--program", required=True, help="Program name to extract")
    ap.add_argument("--out-dir", required=True, help="Output directory for architecture.call.*.json files")
    args = ap.parse_args()

    docs = json.loads(Path(args.input).read_text(encoding="utf-8"))
    calls = [d for d in docs if d.get("type") == "architecture.call" and d.get("program") == args.program]
    if not calls:
        raise SystemExit(f"architecture.call not found for program: {args.program}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for d in calls:
        # Use target + call_type to build a stable filename
        target = (d.get("content") or {}).get("target") or d.get("title")
        call_type = (d.get("content") or {}).get("call_type") or "call"
        safe_target = str(target).replace(" ", "_").replace("/", "_")
        safe_call = str(call_type).replace(" ", "_")
        fname = f"architecture.call.{safe_call}.{safe_target}.json"
        out_path = out_dir / fname
        out_path.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[OK] Wrote {len(calls)} architecture.call.*.json files to {out_dir}")


if __name__ == "__main__":
    main()
