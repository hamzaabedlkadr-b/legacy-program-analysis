#!/usr/bin/env python3
"""
Compare two folders of pdc.json-style graph files and produce a clear report.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


SAMPLE_LIMIT = 12


def die(message: str, code: int = 1) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)
    raise SystemExit(code)


def iter_json_files(root: Path, recursive: bool) -> Iterable[Path]:
    if recursive:
        yield from sorted(path for path in root.rglob("*.json") if path.is_file())
        return
    yield from sorted(path for path in root.glob("*.json") if path.is_file())


def build_index(root: Path, recursive: bool, match_by: str) -> Dict[str, Path]:
    index: Dict[str, Path] = {}
    for path in iter_json_files(root, recursive):
        if match_by == "relative":
            key = str(path.relative_to(root)).replace("\\", "/").upper()
        else:
            key = path.stem.upper()
        prior = index.get(key)
        if prior:
            die(f"Duplicate comparison key {key!r} in {root}: {prior} and {path}")
        index[key] = path
    return index


def load_pdc(path: Path) -> Dict:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except FileNotFoundError:
        die(f"file not found: {path}")
    except json.JSONDecodeError as exc:
        die(f"invalid JSON in {path} (line {exc.lineno}, col {exc.colno})")
    except Exception as exc:
        die(f"failed to read {path}: {exc}")


def extract_graph_sets(data: Dict) -> Tuple[set, set]:
    nodes = {str(node) for node in data.get("nodes", [])}
    edges = set()
    for edge in data.get("edges", []):
        if not isinstance(edge, dict):
            continue
        src = edge.get("from")
        tgt = edge.get("to")
        if src is None or tgt is None:
            continue
        edges.add((str(src), str(tgt)))
    return nodes, edges


def ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return numerator / denominator


def classify_match(
    left_nodes: set,
    right_nodes: set,
    left_edges: set,
    right_edges: set,
) -> str:
    if left_nodes == right_nodes and left_edges == right_edges:
        return "EXACT"
    if left_nodes <= right_nodes and left_edges <= right_edges:
        return "RIGHT_SUPERSET"
    if right_nodes <= left_nodes and right_edges <= left_edges:
        return "LEFT_SUPERSET"
    return "DIFFERENT"


def sample_items(items: List, limit: int = SAMPLE_LIMIT) -> str:
    if not items:
        return "-"
    sample = items[:limit]
    suffix = "" if len(items) <= limit else f" ... (+{len(items) - limit} more)"
    return ", ".join(str(item) for item in sample) + suffix


def write_report(path: Path, lines: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare two folders of pdc.json-style files and write a structural report"
    )
    parser.add_argument("--left", required=True, help="Baseline folder (for example: extension output)")
    parser.add_argument("--right", required=True, help="Candidate folder (for example: no-extension output)")
    parser.add_argument("--report", required=True, help="Path to the output report file")
    parser.add_argument("--left-label", default="LEFT", help="Label shown in the report for the left folder")
    parser.add_argument("--right-label", default="RIGHT", help="Label shown in the report for the right folder")
    parser.add_argument(
        "--match-by",
        choices=["stem", "relative"],
        default="stem",
        help="How to match files between folders (default: stem)",
    )
    parser.add_argument(
        "--non-recursive",
        action="store_true",
        help="Only compare JSON files directly inside each folder",
    )
    args = parser.parse_args()

    left_root = Path(args.left).resolve()
    right_root = Path(args.right).resolve()
    report_path = Path(args.report).resolve()
    recursive = not args.non_recursive

    if not left_root.exists():
        die(f"left folder not found: {left_root}")
    if not left_root.is_dir():
        die(f"left path is not a directory: {left_root}")
    if not right_root.exists():
        die(f"right folder not found: {right_root}")
    if not right_root.is_dir():
        die(f"right path is not a directory: {right_root}")

    left_index = build_index(left_root, recursive, args.match_by)
    right_index = build_index(right_root, recursive, args.match_by)
    all_keys = sorted(set(left_index) | set(right_index))

    exact = 0
    right_superset = 0
    left_superset = 0
    different = 0
    left_only = 0
    right_only = 0

    report_lines: List[str] = [
        "=" * 80,
        "PDC FOLDER COMPARISON REPORT",
        "=" * 80,
        f"{args.left_label:>12} folder: {left_root}",
        f"{args.right_label:>12} folder: {right_root}",
        f"{'Match rule':>12}: {args.match_by}",
        f"{'Recursive':>12}: {'yes' if recursive else 'no'}",
        "",
        "SUMMARY BY FILE",
        "-" * 80,
    ]

    detail_lines: List[str] = []

    for key in all_keys:
        left_path = left_index.get(key)
        right_path = right_index.get(key)

        if left_path and not right_path:
            left_only += 1
            report_lines.append(f"[LEFT ONLY]  {key}")
            continue
        if right_path and not left_path:
            right_only += 1
            report_lines.append(f"[RIGHT ONLY] {key}")
            continue

        assert left_path is not None and right_path is not None

        left_data = load_pdc(left_path)
        right_data = load_pdc(right_path)
        left_nodes, left_edges = extract_graph_sets(left_data)
        right_nodes, right_edges = extract_graph_sets(right_data)

        common_nodes = left_nodes & right_nodes
        common_edges = left_edges & right_edges
        missing_nodes = sorted(left_nodes - right_nodes)
        extra_nodes = sorted(right_nodes - left_nodes)
        missing_edges = sorted(left_edges - right_edges)
        extra_edges = sorted(right_edges - left_edges)

        node_recall = ratio(len(common_nodes), len(left_nodes))
        node_precision = ratio(len(common_nodes), len(right_nodes))
        edge_recall = ratio(len(common_edges), len(left_edges))
        edge_precision = ratio(len(common_edges), len(right_edges))

        status = classify_match(left_nodes, right_nodes, left_edges, right_edges)
        if status == "EXACT":
            exact += 1
        elif status == "RIGHT_SUPERSET":
            right_superset += 1
        elif status == "LEFT_SUPERSET":
            left_superset += 1
        else:
            different += 1

        report_lines.append(
            f"[{status:<14}] {key} | "
            f"nodes {len(left_nodes)} vs {len(right_nodes)} | "
            f"edges {len(left_edges)} vs {len(right_edges)} | "
            f"edge recall={edge_recall:.3f} | edge precision={edge_precision:.3f}"
        )

        if status != "EXACT":
            detail_lines.extend(
                [
                    "",
                    "-" * 80,
                    f"DETAIL: {key}",
                    "-" * 80,
                    f"{args.left_label} file : {left_path}",
                    f"{args.right_label} file: {right_path}",
                    f"Node overlap  : {len(common_nodes)}/{len(left_nodes)} baseline, {len(common_nodes)}/{len(right_nodes)} candidate",
                    f"Edge overlap  : {len(common_edges)}/{len(left_edges)} baseline, {len(common_edges)}/{len(right_edges)} candidate",
                    f"Node recall   : {node_recall:.4f}",
                    f"Node precision: {node_precision:.4f}",
                    f"Edge recall   : {edge_recall:.4f}",
                    f"Edge precision: {edge_precision:.4f}",
                    f"Missing nodes in {args.right_label}: {sample_items(missing_nodes)}",
                    f"Extra nodes in {args.right_label}  : {sample_items(extra_nodes)}",
                    f"Missing edges in {args.right_label}: {sample_items(missing_edges)}",
                    f"Extra edges in {args.right_label}  : {sample_items(extra_edges)}",
                ]
            )

    report_lines.extend(
        [
            "",
            "-" * 80,
            "TOTALS",
            "-" * 80,
            f"Matched files     : {exact + right_superset + left_superset + different}",
            f"Exact matches     : {exact}",
            f"Right supersets   : {right_superset}",
            f"Left supersets    : {left_superset}",
            f"Different matches : {different}",
            f"Only in {args.left_label:<8}: {left_only}",
            f"Only in {args.right_label:<8}: {right_only}",
        ]
    )

    if detail_lines:
        report_lines.extend(["", "DIFFERENCE DETAILS"] + detail_lines)

    write_report(report_path, report_lines)

    for line in report_lines:
        print(line)
    print("")
    print(f"[DONE] Report written to {report_path}")


if __name__ == "__main__":
    main()
