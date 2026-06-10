#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from build_jcl_artifacts import parse_jcl


def collect_jcl_files(root: Path) -> List[Path]:
    files: List[Path] = []
    seen = set()
    for pattern in ("*.JCL", "*.jcl"):
        for path in sorted(root.glob(pattern)):
            key = str(path.resolve()).upper()
            if key in seen:
                continue
            seen.add(key)
            files.append(path)
    return files


def build_proc_catalog(parsed_files: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    catalog: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in parsed_files:
        path = item["path"]
        data = item["data"]
        for proc in data.get("local_procedures", []):
            catalog[proc["procedure"]].append(
                {
                    "source": str(path),
                    "job": data.get("job_name"),
                    "procedure": proc["procedure"],
                    "programs": proc.get("programs", []),
                    "steps_count": proc.get("steps_count", 0),
                }
            )
    return catalog


def collect_unknown_dd_usage(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    for step in data.get("steps", []):
        for dd in step.get("dds", []):
            if dd.get("access_type") != "unknown":
                continue
            if not dd.get("dsn"):
                continue
            issues.append(
                {
                    "step": step["step"],
                    "program": step.get("program"),
                    "proc": step.get("proc"),
                    "ddname": dd.get("ddname"),
                    "dsn": dd.get("dsn"),
                    "disp": dd.get("disp"),
                    "raw": dd.get("raw"),
                    "source_lines": dd.get("source_lines"),
                }
            )
    return issues


def validate_file(
    path: Path,
    data: Dict[str, Any],
    proc_catalog: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    raw_unresolved = data.get("unresolved_procedures", [])
    batch_resolvable: List[Dict[str, Any]] = []
    unresolved_after_batch: List[str] = []

    for proc in raw_unresolved:
        candidates = [
            item
            for item in proc_catalog.get(proc, [])
            if Path(item["source"]).resolve() != path.resolve()
        ]
        if candidates:
            batch_resolvable.append(
                {
                    "procedure": proc,
                    "candidates": candidates,
                }
            )
        else:
            unresolved_after_batch.append(proc)

    zero_parsed_programs = len(data.get("programs", [])) == 0
    unknown_dd_usage = collect_unknown_dd_usage(data)

    flags: List[Dict[str, str]] = []
    if batch_resolvable:
        flags.append(
            {
                "kind": "procedure_resolvable_in_batch",
                "severity": "info",
                "message": (
                    f"{len(batch_resolvable)} procedure reference(s) are unresolved in-file "
                    f"but have candidate PROC definitions elsewhere in the batch."
                ),
            }
        )
    if unresolved_after_batch:
        flags.append(
            {
                "kind": "unresolved_procedure",
                "severity": "warning",
                "message": (
                    f"{len(unresolved_after_batch)} procedure reference(s) remain unresolved "
                    f"after batch-wide PROC lookup."
                ),
            }
        )
    if zero_parsed_programs:
        flags.append(
            {
                "kind": "zero_parsed_programs",
                "severity": "warning",
                "message": "No executable programs were parsed from this JCL file.",
            }
        )
    if unknown_dd_usage:
        flags.append(
            {
                "kind": "unknown_dd_usage",
                "severity": "warning",
                "message": (
                    f"{len(unknown_dd_usage)} DD statement(s) still have ambiguous access type."
                ),
            }
        )

    return {
        "source": str(path),
        "job": data.get("job_name"),
        "purpose": data.get("purpose"),
        "warnings": data.get("warnings", []),
        "programs": data.get("programs", []),
        "procedures": data.get("procedures", []),
        "local_procedures": data.get("local_procedures", []),
        "symbols": data.get("symbols", {}),
        "control_statements_count": len(data.get("control_statements", [])),
        "execution_steps_count": len(data.get("execution_steps", [])),
        "datasets_count": len(data.get("datasets", [])),
        "raw_unresolved_procedures": raw_unresolved,
        "batch_resolvable_procedures": batch_resolvable,
        "unresolved_procedures": unresolved_after_batch,
        "zero_parsed_programs": zero_parsed_programs,
        "unknown_dd_usage": unknown_dd_usage,
        "flags": flags,
        "status": "warning" if any(flag["severity"] == "warning" for flag in flags) else "ok",
    }


def build_summary(results: List[Dict[str, Any]], parse_errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    warnings = [item for item in results if item["status"] == "warning"]
    return {
        "files_checked": len(results) + len(parse_errors),
        "files_parsed": len(results),
        "parse_errors": len(parse_errors),
        "files_with_flags": len([item for item in results if item["flags"]]),
        "files_with_warnings": len(warnings),
        "files_with_unresolved_procedures": len(
            [item for item in results if item["unresolved_procedures"]]
        ),
        "files_with_batch_resolvable_procedures": len(
            [item for item in results if item["batch_resolvable_procedures"]]
        ),
        "files_with_zero_parsed_programs": len(
            [item for item in results if item["zero_parsed_programs"]]
        ),
        "files_with_unknown_dd_usage": len(
            [item for item in results if item["unknown_dd_usage"]]
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Build a batch validation report for a folder of JCL files. "
            "Flags unresolved procedures, zero parsed programs, and ambiguous DD usage."
        )
    )
    ap.add_argument("--jcl-dir", required=True, help="Folder containing JCL files")
    ap.add_argument("--output", help="Output JSON path")
    args = ap.parse_args()

    jcl_dir = Path(args.jcl_dir)
    if not jcl_dir.exists():
        raise SystemExit(f"JCL dir not found: {jcl_dir}")
    if not jcl_dir.is_dir():
        raise SystemExit(f"JCL path is not a directory: {jcl_dir}")

    output_path = Path(args.output) if args.output else jcl_dir / "jcl.validation.report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    jcl_files = collect_jcl_files(jcl_dir)
    if not jcl_files:
        raise SystemExit(f"No JCL files found in: {jcl_dir}")

    parsed_files: List[Dict[str, Any]] = []
    parse_errors: List[Dict[str, Any]] = []

    for path in jcl_files:
        try:
            parsed_files.append({"path": path, "data": parse_jcl(path)})
        except Exception as exc:
            parse_errors.append(
                {
                    "source": str(path),
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    proc_catalog = build_proc_catalog(parsed_files)

    results = [
        validate_file(item["path"], item["data"], proc_catalog)
        for item in parsed_files
    ]
    results.sort(key=lambda item: item["source"].upper())

    proc_catalog_list = [
        {
            "procedure": proc,
            "definitions": sorted(entries, key=lambda item: item["source"].upper()),
        }
        for proc, entries in sorted(proc_catalog.items())
    ]

    report = {
        "type": "jcl.validation.report",
        "jcl_dir": str(jcl_dir),
        "summary": build_summary(results, parse_errors),
        "procedure_catalog": proc_catalog_list,
        "files": results,
        "parse_errors": parse_errors,
    }

    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = report["summary"]
    print(
        "[OK] Wrote JCL validation report to "
        f"{output_path} "
        f"(files={summary['files_checked']}, warnings={summary['files_with_warnings']}, "
        f"parse_errors={summary['parse_errors']})"
    )


if __name__ == "__main__":
    main()
