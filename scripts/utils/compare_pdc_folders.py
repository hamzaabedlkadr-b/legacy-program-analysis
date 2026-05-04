#!/usr/bin/env python3
"""
Compare two folders of pdc.json-style graph files and produce a concise scorecard.
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


SAMPLE_LIMIT = 8
DEFAULT_TOP_DIFFERENCES = 15


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
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except FileNotFoundError:
        die(f"file not found: {path}")
    except json.JSONDecodeError as exc:
        die(f"invalid JSON in {path} (line {exc.lineno}, col {exc.colno})")
    except Exception as exc:
        die(f"failed to read {path}: {exc}")
    if not isinstance(data, dict):
        die(f"expected top-level JSON object in {path}, found {type(data).__name__}")
    return data


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


def f1_score(recall_value: float, precision_value: float) -> float:
    total = recall_value + precision_value
    if total == 0:
        return 0.0
    return 2 * recall_value * precision_value / total


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


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


@dataclass
class FileComparison:
    key: str
    status: str
    left_path: Optional[Path]
    right_path: Optional[Path]
    left_node_count: int
    right_node_count: int
    common_node_count: int
    left_edge_count: int
    right_edge_count: int
    common_edge_count: int
    node_recall: float
    node_precision: float
    node_f1: float
    edge_recall: float
    edge_precision: float
    edge_f1: float
    missing_nodes: List[str]
    extra_nodes: List[str]
    missing_edges: List[Tuple[str, str]]
    extra_edges: List[Tuple[str, str]]


def compare_file_pair(key: str, left_path: Optional[Path], right_path: Optional[Path]) -> FileComparison:
    left_data = load_pdc(left_path) if left_path else {}
    right_data = load_pdc(right_path) if right_path else {}

    left_nodes, left_edges = extract_graph_sets(left_data)
    right_nodes, right_edges = extract_graph_sets(right_data)
    common_nodes = left_nodes & right_nodes
    common_edges = left_edges & right_edges
    missing_nodes = sorted(left_nodes - right_nodes)
    extra_nodes = sorted(right_nodes - left_nodes)
    missing_edges = sorted(left_edges - right_edges)
    extra_edges = sorted(right_edges - left_edges)

    if left_path and not right_path:
        status = "LEFT_ONLY"
    elif right_path and not left_path:
        status = "RIGHT_ONLY"
    else:
        status = classify_match(left_nodes, right_nodes, left_edges, right_edges)

    node_recall = ratio(len(common_nodes), len(left_nodes))
    node_precision = ratio(len(common_nodes), len(right_nodes))
    edge_recall = ratio(len(common_edges), len(left_edges))
    edge_precision = ratio(len(common_edges), len(right_edges))

    return FileComparison(
        key=key,
        status=status,
        left_path=left_path,
        right_path=right_path,
        left_node_count=len(left_nodes),
        right_node_count=len(right_nodes),
        common_node_count=len(common_nodes),
        left_edge_count=len(left_edges),
        right_edge_count=len(right_edges),
        common_edge_count=len(common_edges),
        node_recall=node_recall,
        node_precision=node_precision,
        node_f1=f1_score(node_recall, node_precision),
        edge_recall=edge_recall,
        edge_precision=edge_precision,
        edge_f1=f1_score(edge_recall, edge_precision),
        missing_nodes=missing_nodes,
        extra_nodes=extra_nodes,
        missing_edges=missing_edges,
        extra_edges=extra_edges,
    )


def profile_candidate(
    edge_recall: float,
    edge_precision: float,
    left_only: int,
    right_only: int,
    left_label: str,
    right_label: str,
) -> str:
    if edge_recall >= 0.99 and edge_precision >= 0.99 and left_only == 0 and right_only == 0:
        return f"{right_label} is effectively identical to {left_label}."
    if edge_recall >= edge_precision + 0.05:
        return (
            f"{right_label} is more expansive than {left_label}: it keeps most baseline structure "
            f"but also adds extra nodes or edges."
        )
    if edge_precision >= edge_recall + 0.05:
        return (
            f"{right_label} is more conservative than {left_label}: it stays tighter, "
            f"but it also misses more baseline structure."
        )
    if edge_recall >= 0.90 and edge_precision >= 0.90:
        return f"{right_label} stays very close to {left_label} overall."
    if edge_recall >= 0.75 and edge_precision >= 0.75:
        return f"{right_label} is moderately close to {left_label}, with meaningful differences."
    return f"{right_label} differs substantially from {left_label}."


def score_hint(
    alignment_score: float,
    edge_recall: float,
    edge_precision: float,
    left_label: str,
    right_label: str,
) -> str:
    if alignment_score >= 0.95:
        return (
            f"If your goal is to reproduce {left_label}, {right_label} performed very well."
        )
    if alignment_score >= 0.85:
        return (
            f"If your goal is to reproduce {left_label}, {right_label} performed reasonably well."
        )
    if edge_recall > edge_precision:
        return (
            f"{right_label} favors coverage over strict agreement with {left_label}."
        )
    if edge_precision > edge_recall:
        return (
            f"{right_label} favors strict agreement over full coverage of {left_label}."
        )
    return f"{right_label} is not clearly better or worse without an external ground truth."


def build_detail_lines(comparison: FileComparison, left_label: str, right_label: str) -> List[str]:
    lines = [
        f"{comparison.key} [{comparison.status}]",
        f"  node F1={pct(comparison.node_f1)} | recall={pct(comparison.node_recall)} | precision={pct(comparison.node_precision)} | left/right={comparison.left_node_count}/{comparison.right_node_count}",
        f"  edge F1={pct(comparison.edge_f1)} | recall={pct(comparison.edge_recall)} | precision={pct(comparison.edge_precision)} | left/right={comparison.left_edge_count}/{comparison.right_edge_count}",
    ]

    if comparison.left_path:
        lines.append(f"  {left_label} file : {comparison.left_path}")
    if comparison.right_path:
        lines.append(f"  {right_label} file: {comparison.right_path}")

    if comparison.status != "EXACT":
        lines.extend(
            [
                f"  missing nodes in {right_label}: {sample_items(comparison.missing_nodes)}",
                f"  extra nodes in {right_label}  : {sample_items(comparison.extra_nodes)}",
                f"  missing edges in {right_label}: {sample_items(comparison.missing_edges)}",
                f"  extra edges in {right_label}  : {sample_items(comparison.extra_edges)}",
            ]
        )

    return lines


def status_sort_key(comparison: FileComparison) -> Tuple[int, float, float, str]:
    priority = {
        "LEFT_ONLY": 0,
        "RIGHT_ONLY": 1,
        "DIFFERENT": 2,
        "LEFT_SUPERSET": 3,
        "RIGHT_SUPERSET": 4,
        "EXACT": 5,
    }
    return (
        priority.get(comparison.status, 99),
        comparison.edge_f1,
        comparison.node_f1,
        comparison.key,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare two folders of pdc.json-style files and write a structural scorecard"
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
    parser.add_argument(
        "--top-differences",
        type=int,
        default=DEFAULT_TOP_DIFFERENCES,
        help=f"How many worst mismatches to include in the report (default: {DEFAULT_TOP_DIFFERENCES})",
    )
    parser.add_argument(
        "--show-all-files",
        action="store_true",
        help="Include one summary line for every file in the report",
    )
    parser.add_argument(
        "--full-details",
        action="store_true",
        help="Append full detail blocks for every non-exact file",
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
    if args.top_differences < 0:
        die("top-differences must be >= 0")

    left_index = build_index(left_root, recursive, args.match_by)
    right_index = build_index(right_root, recursive, args.match_by)
    all_keys = sorted(set(left_index) | set(right_index))

    exact = 0
    right_superset = 0
    left_superset = 0
    different = 0
    left_only = 0
    right_only = 0
    matched_pairs = 0

    total_left_nodes = 0
    total_right_nodes = 0
    total_common_nodes = 0
    total_left_edges = 0
    total_right_edges = 0
    total_common_edges = 0

    comparisons: List[FileComparison] = []

    for key in all_keys:
        comparison = compare_file_pair(key, left_index.get(key), right_index.get(key))
        comparisons.append(comparison)

        total_left_nodes += comparison.left_node_count
        total_right_nodes += comparison.right_node_count
        total_common_nodes += comparison.common_node_count
        total_left_edges += comparison.left_edge_count
        total_right_edges += comparison.right_edge_count
        total_common_edges += comparison.common_edge_count

        if comparison.status == "EXACT":
            exact += 1
            matched_pairs += 1
        elif comparison.status == "RIGHT_SUPERSET":
            right_superset += 1
            matched_pairs += 1
        elif comparison.status == "LEFT_SUPERSET":
            left_superset += 1
            matched_pairs += 1
        elif comparison.status == "DIFFERENT":
            different += 1
            matched_pairs += 1
        elif comparison.status == "LEFT_ONLY":
            left_only += 1
        elif comparison.status == "RIGHT_ONLY":
            right_only += 1

    overall_node_recall = ratio(total_common_nodes, total_left_nodes)
    overall_node_precision = ratio(total_common_nodes, total_right_nodes)
    overall_edge_recall = ratio(total_common_edges, total_left_edges)
    overall_edge_precision = ratio(total_common_edges, total_right_edges)
    overall_node_f1 = f1_score(overall_node_recall, overall_node_precision)
    overall_edge_f1 = f1_score(overall_edge_recall, overall_edge_precision)
    alignment_score = (overall_node_f1 + overall_edge_f1) / 2

    exact_rate = ratio(exact, matched_pairs)
    left_only_items = sorted(c.key for c in comparisons if c.status == "LEFT_ONLY")
    right_only_items = sorted(c.key for c in comparisons if c.status == "RIGHT_ONLY")
    non_exact = [c for c in comparisons if c.status != "EXACT"]
    worst_differences = sorted(non_exact, key=status_sort_key)[: args.top_differences]

    report_lines: List[str] = [
        "=" * 80,
        "PDC FOLDER COMPARISON SCORECARD",
        "=" * 80,
        f"{args.left_label:>12} folder: {left_root}",
        f"{args.right_label:>12} folder: {right_root}",
        f"{'Match rule':>12}: {args.match_by}",
        f"{'Recursive':>12}: {'yes' if recursive else 'no'}",
        "",
        "EXECUTIVE SUMMARY",
        "-" * 80,
        f"Reference folder          : {args.left_label}",
        f"Candidate folder          : {args.right_label}",
        f"Overall alignment score   : {pct(alignment_score)}",
        f"Exact match rate          : {pct(exact_rate)} of matched files",
        f"Reference coverage        : nodes {pct(overall_node_recall)} | edges {pct(overall_edge_recall)}",
        f"Candidate agreement       : nodes {pct(overall_node_precision)} | edges {pct(overall_edge_precision)}",
        f"Candidate profile         : {profile_candidate(overall_edge_recall, overall_edge_precision, left_only, right_only, args.left_label, args.right_label)}",
        f"Decision hint             : {score_hint(alignment_score, overall_edge_recall, overall_edge_precision, args.left_label, args.right_label)}",
        "",
        "FILE STATUS TOTALS",
        "-" * 80,
        f"Files compared by key     : {len(all_keys)}",
        f"Matched pairs             : {matched_pairs}",
        f"Exact matches             : {exact}",
        f"{args.right_label} supersets     : {right_superset}",
        f"{args.left_label} supersets      : {left_superset}",
        f"Different matched files   : {different}",
        f"Only in {args.left_label:<16}: {left_only}",
        f"Only in {args.right_label:<16}: {right_only}",
        "",
        "GRAPH TOTALS",
        "-" * 80,
        f"{args.left_label} total nodes      : {total_left_nodes}",
        f"{args.right_label} total nodes     : {total_right_nodes}",
        f"Common nodes             : {total_common_nodes}",
        f"{args.left_label} total edges      : {total_left_edges}",
        f"{args.right_label} total edges     : {total_right_edges}",
        f"Common edges             : {total_common_edges}",
    ]

    if left_only_items:
        report_lines.extend(
            [
                "",
                f"{args.left_label}-ONLY SAMPLE",
                "-" * 80,
                sample_items(left_only_items),
            ]
        )

    if right_only_items:
        report_lines.extend(
            [
                "",
                f"{args.right_label}-ONLY SAMPLE",
                "-" * 80,
                sample_items(right_only_items),
            ]
        )

    if worst_differences:
        report_lines.extend(["", "TOP DIFFERENCES", "-" * 80])
        for idx, comparison in enumerate(worst_differences, 1):
            report_lines.append(
                f"{idx:>2}. {comparison.key} [{comparison.status}] | "
                f"edge F1={pct(comparison.edge_f1)} | "
                f"recall={pct(comparison.edge_recall)} | "
                f"precision={pct(comparison.edge_precision)}"
            )
            report_lines.append(
                f"    nodes left/right/common={comparison.left_node_count}/{comparison.right_node_count}/{comparison.common_node_count} | "
                f"edges left/right/common={comparison.left_edge_count}/{comparison.right_edge_count}/{comparison.common_edge_count}"
            )
            report_lines.append(
                f"    missing edges in {args.right_label}: {sample_items(comparison.missing_edges)}"
            )
            report_lines.append(
                f"    extra edges in {args.right_label}  : {sample_items(comparison.extra_edges)}"
            )

    if args.show_all_files:
        report_lines.extend(["", "ALL FILE STATUSES", "-" * 80])
        for comparison in comparisons:
            report_lines.append(
                f"[{comparison.status:<14}] {comparison.key} | "
                f"edge F1={pct(comparison.edge_f1)} | "
                f"recall={pct(comparison.edge_recall)} | "
                f"precision={pct(comparison.edge_precision)}"
            )

    if args.full_details and non_exact:
        report_lines.extend(["", "FULL DIFFERENCE DETAILS", "-" * 80])
        for comparison in sorted(non_exact, key=status_sort_key):
            report_lines.extend(build_detail_lines(comparison, args.left_label, args.right_label))
            report_lines.append("")

    write_report(report_path, report_lines)

    for line in report_lines:
        print(line)
    print("")
    print(f"[DONE] Report written to {report_path}")


if __name__ == "__main__":
    main()
