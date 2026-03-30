import json
import re
import sys
from pathlib import Path


def die(msg: str, code: int = 1) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    raise SystemExit(code)


def main() -> None:
    dot_path = Path("dott.txt")
    out_path = Path("pdc.json")

    try:
        text = dot_path.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        die(f"input file not found: {dot_path}")
    except Exception as exc:
        die(f"failed to read {dot_path}: {exc}")

    # Graph name: digraph A { ... }
    m = re.search(r"digraph\s+([A-Za-z0-9_]+)\s*\{", text)
    graph_name = m.group(1) if m else "G"

    # rankdir=LR (optional)
    m = re.search(r"rankdir\s*=\s*([A-Za-z]+)\s*;", text)
    rankdir = m.group(1) if m else None

    # Edges like: <A>-><B>;
    edge_pattern = re.compile(r"<([^>]+)>\s*->\s*<([^>]+)>\s*;")

    nodes = set()
    edges = []

    for a, b in edge_pattern.findall(text):
        nodes.add(a)
        nodes.add(b)
        edges.append({"from": a, "to": b})

    data = {
        "graph": {"name": graph_name, "rankdir": rankdir},
        "nodes": sorted(nodes),
        "edges": edges,
    }

    try:
        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        die(f"failed to write {out_path}: {exc}")
    print(f"Wrote {out_path} with {len(nodes)} nodes and {len(edges)} edges.")

if __name__ == "__main__":
    main()
