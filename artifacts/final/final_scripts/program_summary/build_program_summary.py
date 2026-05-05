#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def canonical_program(value):
    text = str(value or "").strip().upper()
    if not text:
        return ""
    leaf = text.replace("\\", "/").rstrip("/").split("/")[-1]
    if "." in leaf:
        leaf = leaf.rsplit(".", 1)[0]
    return leaf or text


def main():
    ap = argparse.ArgumentParser(description="Extract program.summary from rag_documents.json")
    ap.add_argument("--input", required=True, help="Path to rag_documents.json")
    ap.add_argument("--program", required=True, help="Program name to extract")
    ap.add_argument("--output", required=True, help="Output program.summary.json path")
    args = ap.parse_args()

    docs = json.loads(Path(args.input).read_text(encoding="utf-8"))
    wanted = canonical_program(args.program)
    matches = [
        d
        for d in docs
        if d.get("type") == "program.summary" and canonical_program(d.get("program")) == wanted
    ]
    if not matches:
        available = sorted(
            {canonical_program(d.get("program")) for d in docs if d.get("type") == "program.summary"}
        )
        suffix = f" Available program summaries: {', '.join(available)}" if available else ""
        raise SystemExit(f"program.summary not found for program: {args.program}.{suffix}")

    out = dict(matches[0])
    out["program"] = args.program
    Path(args.output).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Wrote {args.output}")


if __name__ == "__main__":
    main()
