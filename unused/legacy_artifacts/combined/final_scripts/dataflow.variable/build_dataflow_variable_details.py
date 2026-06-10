#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from pathlib import Path


SAFE_RE = re.compile(r"[^A-Z0-9-]+")


def make_id(text: str) -> str:
    return hashlib.blake2b(text.encode("utf-8"), digest_size=8).hexdigest()


def safe_name(var: str) -> str:
    v = var.upper()
    v = SAFE_RE.sub("_", v).strip("_")
    return v or "VAR"


def list_or_none(items):
    if not items:
        return "none"
    return ", ".join(items)


def main():
    ap = argparse.ArgumentParser(description="Build dataflow.variable.*.json from pdc_var_index_used.json")
    ap.add_argument("--input", required=True, help="Path to pdc_var_index_used.json")
    ap.add_argument("--program", required=True, help="Program name")
    ap.add_argument("--out-dir", required=True, help="Output directory for dataflow.variable.*.json files")
    args = ap.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    wrote = 0
    for v in data:
        var = v.get("variable") or "UNKNOWN"
        origin = v.get("origin") or "UNKNOWN"
        defined_in = v.get("defined_in") or []
        modified_in = v.get("modified_in") or []
        used_in = v.get("used_in") or []
        controls_flow = bool(v.get("controls_flow"))
        fanout_nodes = v.get("fanout_nodes") or []

        evidence = v.get("evidence") or {}
        write_sites = evidence.get("write_sites") or []
        read_sites = evidence.get("read_sites") or []
        control_sites = evidence.get("control_sites") or []

        embedding_text = (
            f"{args.program} variable {var}. "
            f"Origin={origin}. "
            f"Defined in: {list_or_none(defined_in)}. "
            f"Modified in: {list_or_none(modified_in)}. "
            f"Used in: {list_or_none(used_in)}. "
            f"Controls flow: {'yes' if controls_flow else 'no'}. "
            f"Fanout nodes: {list_or_none(fanout_nodes)}."
        )

        doc = {
            "id": make_id(f"{args.program}|{var}"),
            "type": "dataflow.variable",
            "program": args.program,
            "title": f"{args.program} variable {var}",
            "embedding_text": embedding_text,
            "content": v,
            "meta": {
                "origin": origin,
                "controls_flow": controls_flow,
                "counts": {
                    "defined_in": len(defined_in),
                    "modified_in": len(modified_in),
                    "used_in": len(used_in),
                    "fanout_nodes": len(fanout_nodes),
                    "write_sites": len(write_sites),
                    "read_sites": len(read_sites),
                    "control_sites": len(control_sites),
                },
            },
        }

        out_path = out_dir / f"dataflow.variable.{safe_name(var)}.json"
        out_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        wrote += 1

    print(f"[OK] Wrote {wrote} dataflow.variable.*.json files to {out_dir}")


if __name__ == "__main__":
    main()
