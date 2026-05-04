#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, List, Sequence


EXPECTED_TOP_KEYS = {"graph", "nodes", "edges"}
EXPECTED_GRAPH_KEYS = {"name", "rankdir"}
EXPECTED_EDGE_KEYS = {"from", "to"}


def die(message: str, code: int = 1) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)
    raise SystemExit(code)


def iter_json_files(path: Path, recursive: bool) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    if recursive:
        yield from sorted(item for item in path.rglob("*.json") if item.is_file())
        return
    yield from sorted(item for item in path.glob("*.json") if item.is_file())


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except FileNotFoundError:
        die(f"file not found: {path}")
    except json.JSONDecodeError as exc:
        return {"__load_error__": f"invalid JSON (line {exc.lineno}, col {exc.colno})"}
    except Exception as exc:
        return {"__load_error__": f"failed to read file: {exc}"}


def add_error(errors: List[str], message: str) -> None:
    if message not in errors:
        errors.append(message)


def validate_pdc_json(data: Any, strict: bool) -> List[str]:
    errors: List[str] = []

    if isinstance(data, dict) and "__load_error__" in data:
        return [str(data["__load_error__"])]

    if not isinstance(data, dict):
        return [f"top-level JSON must be an object, found {type(data).__name__}"]

    missing_top = sorted(EXPECTED_TOP_KEYS - set(data))
    if missing_top:
        add_error(errors, f"missing top-level keys: {', '.join(missing_top)}")

    if strict:
        extra_top = sorted(set(data) - EXPECTED_TOP_KEYS)
        if extra_top:
            add_error(errors, f"unexpected top-level keys: {', '.join(extra_top)}")

    graph = data.get("graph")
    if not isinstance(graph, dict):
        add_error(errors, "graph must be an object")
    else:
        missing_graph = sorted(EXPECTED_GRAPH_KEYS - set(graph))
        if missing_graph:
            add_error(errors, f"missing graph keys: {', '.join(missing_graph)}")

        if strict:
            extra_graph = sorted(set(graph) - EXPECTED_GRAPH_KEYS)
            if extra_graph:
                add_error(errors, f"unexpected graph keys: {', '.join(extra_graph)}")

        name = graph.get("name")
        if not isinstance(name, str) or not name.strip():
            add_error(errors, "graph.name must be a non-empty string")

        rankdir = graph.get("rankdir")
        if rankdir is not None and not isinstance(rankdir, str):
            add_error(errors, "graph.rankdir must be a string or null")

    nodes = data.get("nodes")
    if not isinstance(nodes, list):
        add_error(errors, "nodes must be a list")
    else:
        bad_nodes = [idx for idx, node in enumerate(nodes) if not isinstance(node, str)]
        if bad_nodes:
            add_error(errors, f"nodes must contain only strings (bad indexes: {sample_indexes(bad_nodes)})")

    edges = data.get("edges")
    if not isinstance(edges, list):
        add_error(errors, "edges must be a list")
    else:
        bad_edges: List[str] = []
        for idx, edge in enumerate(edges):
            if not isinstance(edge, dict):
                bad_edges.append(f"{idx}:not-object")
                continue

            missing_edge = sorted(EXPECTED_EDGE_KEYS - set(edge))
            if missing_edge:
                bad_edges.append(f"{idx}:missing {','.join(missing_edge)}")
                continue

            if strict:
                extra_edge = sorted(set(edge) - EXPECTED_EDGE_KEYS)
                if extra_edge:
                    bad_edges.append(f"{idx}:extra {','.join(extra_edge)}")
                    continue

            src = edge.get("from")
            tgt = edge.get("to")
            if not isinstance(src, str) or not isinstance(tgt, str):
                bad_edges.append(f"{idx}:from/to must be strings")

        if bad_edges:
            add_error(errors, f"invalid edge entries: {sample_items(bad_edges)}")

    return errors


def sample_items(items: Sequence[str], limit: int = 8) -> str:
    sample = list(items[:limit])
    suffix = "" if len(items) <= limit else f" ... (+{len(items) - limit} more)"
    return ", ".join(sample) + suffix


def sample_indexes(items: Sequence[int], limit: int = 8) -> str:
    sample = [str(i) for i in items[:limit]]
    suffix = "" if len(items) <= limit else f" ... (+{len(items) - limit} more)"
    return ", ".join(sample) + suffix


def write_invalid_report(out_path: Path, invalid_entries: List[tuple[str, List[str]]]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.suffix.lower() == ".json":
        payload = [
            {"path": path, "errors": errors}
            for path, errors in invalid_entries
        ]
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return

    lines: List[str] = []
    for path, errors in invalid_entries:
        lines.append(path)
        for error in errors:
            lines.append(f"  - {error}")
    out_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate that JSON files match the pdc.json graph/nodes/edges shape."
    )
    ap.add_argument("--path", required=True, help="A JSON file or a folder containing JSON files")
    ap.add_argument("--recursive", action="store_true", help="Scan folders recursively")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Reject extra keys and require edge objects to contain only from/to",
    )
    ap.add_argument(
        "--write-invalid",
        help="Optional output file for invalid entries (.txt or .json)",
    )
    ap.add_argument(
        "--fail-on-invalid",
        action="store_true",
        help="Exit with code 2 if any file is invalid",
    )
    args = ap.parse_args()

    input_path = Path(args.path)
    if not input_path.exists():
        die(f"path not found: {input_path}")
    if input_path.is_dir():
        files = list(iter_json_files(input_path, args.recursive))
        if not files:
            die(f"no JSON files found in: {input_path}")
    else:
        if input_path.suffix.lower() != ".json":
            die(f"expected a .json file, got: {input_path}")
        files = [input_path]

    valid_count = 0
    invalid_entries: List[tuple[str, List[str]]] = []

    for path in files:
        data = load_json(path)
        errors = validate_pdc_json(data, strict=args.strict)
        rel = str(path.relative_to(input_path)) if input_path.is_dir() else str(path)
        if errors:
            invalid_entries.append((rel, errors))
            print(f"[INVALID] {rel}")
            for error in errors:
                print(f"  - {error}")
            continue
        valid_count += 1

    print(f"[INFO] checked files: {len(files)}")
    print(f"[INFO] valid files  : {valid_count}")
    print(f"[INFO] invalid files: {len(invalid_entries)}")

    if args.write_invalid:
        out_path = Path(args.write_invalid)
        write_invalid_report(out_path, invalid_entries)
        print(f"[OK] wrote invalid report: {out_path}")

    if args.fail_on_invalid and invalid_entries:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
