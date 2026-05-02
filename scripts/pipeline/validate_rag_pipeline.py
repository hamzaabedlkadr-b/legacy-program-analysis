#!/usr/bin/env python3
"""Validate per-program packages and generated RAG pipeline outputs."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_ARTIFACT_FILES = {
    "program_summary": "program.summary.json",
    "architecture_copybooks": "architecture.copybooks.json",
    "architecture_calls": "architecture.calls.json",
    "controlflow_cfg": "controlflow.cfg.json",
    "dataflow_used_variables": "dataflow.used_variables.json",
    "program_comments": "program.comments.json",
    "ui_cics_navigation": "ui.cics.navigation.json",
}

DETAIL_DIRS = {
    "architecture_call": "architecture.call",
    "architecture_sqlinclude": "architecture.sqlinclude",
    "architecture_db2_table": "architecture.db2_table",
    "dataflow_variable": "dataflow.variable",
    "business_rule": "business_rule",
    "program_comments_detail": "program.comments",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a compact validation report for RAG packages/output.")
    parser.add_argument("--package-root", type=Path, help="Folder containing per-program input packages.")
    parser.add_argument(
        "--out-root",
        type=Path,
        help="Pipeline output root. Can be the folder containing programs/ or programs/ itself.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Destination folder for rag_validation_report.json and .md.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def resolve_programs_dir(out_root: Path | None) -> Path | None:
    if not out_root:
        return None
    if (out_root / "programs").is_dir():
        return out_root / "programs"
    if out_root.is_dir() and any((child / "artifacts").is_dir() for child in out_root.iterdir() if child.is_dir()):
        return out_root
    return None


def discover_package_dirs(package_root: Path | None) -> dict[str, Path]:
    if not package_root or not package_root.is_dir():
        return {}
    packages: dict[str, Path] = {}
    candidates = [package_root] + sorted(child for child in package_root.iterdir() if child.is_dir())
    for candidate in candidates:
        if (candidate / "cobol").is_dir():
            packages[candidate.name.upper()] = candidate
    return packages


def discover_output_dirs(out_root: Path | None) -> dict[str, Path]:
    programs_dir = resolve_programs_dir(out_root)
    if not programs_dir:
        return {}
    return {child.name.upper(): child for child in sorted(programs_dir.iterdir()) if child.is_dir()}


def count_files(root: Path, patterns: list[str]) -> int:
    seen: set[str] = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file():
                seen.add(str(path.resolve()).lower())
    return len(seen)


def package_status(package_dir: Path | None) -> dict[str, Any]:
    if not package_dir:
        return {
            "exists": False,
            "has_mapa": None,
            "has_controlflow": None,
            "copybooks": {"status": "unknown", "present_count": 0, "missing_count": None, "missing": []},
            "manifest_valid": None,
        }

    manifest_path = package_dir / "manifest.json"
    manifest: dict[str, Any] = {}
    manifest_valid = None
    if manifest_path.is_file():
        try:
            manifest = load_json(manifest_path)
            manifest_valid = True
        except Exception:
            manifest_valid = False

    copybook_files = count_files(package_dir / "copybooks", ["*.cpy", "*.CPY", "*.copy", "*.COPY", "*.cob", "*.COB"]) if (package_dir / "copybooks").is_dir() else 0
    mapa_files = count_files(package_dir / "mapa", ["*.txt", "*.TXT", "*.csv", "*.CSV"]) if (package_dir / "mapa").is_dir() else 0
    cfg_files = count_files(package_dir / "controlflow", ["*.json", "*.JSON"]) if (package_dir / "controlflow").is_dir() else 0

    missing_copybooks = []
    if manifest:
        missing_copybooks = list((manifest.get("missing") or {}).get("copybooks") or [])

    copybook_status = "complete"
    if copybook_files == 0:
        copybook_status = "none"
    elif missing_copybooks:
        copybook_status = "missing"

    return {
        "exists": True,
        "has_mapa": mapa_files > 0,
        "has_controlflow": cfg_files > 0,
        "mapa_count": mapa_files,
        "controlflow_count": cfg_files,
        "copybooks": {
            "status": copybook_status,
            "present_count": copybook_files,
            "missing_count": len(missing_copybooks),
            "missing": missing_copybooks,
        },
        "manifest_valid": manifest_valid,
    }


def validate_json_tree(root: Path | None) -> dict[str, Any]:
    if not root or not root.exists():
        return {"valid": None, "files_checked": 0, "invalid_files": []}

    invalid: list[dict[str, str]] = []
    checked = 0
    for path in sorted(root.rglob("*.json")):
        checked += 1
        try:
            load_json(path)
        except Exception as exc:
            invalid.append({"path": str(path), "error": str(exc)})
    return {"valid": len(invalid) == 0, "files_checked": checked, "invalid_files": invalid}


def output_status(output_dir: Path | None) -> dict[str, Any]:
    if not output_dir:
        return {
            "exists": False,
            "json": {"valid": None, "files_checked": 0, "invalid_files": []},
            "required_artifacts": {},
            "artifact_counts": {},
        }

    artifacts_dir = output_dir / "artifacts"
    inputs_dir = output_dir / "inputs"
    required = {
        key: (artifacts_dir / filename).is_file()
        for key, filename in REQUIRED_ARTIFACT_FILES.items()
    }
    required["input_rag_documents"] = (inputs_dir / "rag_documents.json").is_file()

    counts = {
        "artifact_json_total": count_files(artifacts_dir, ["*.json", "*/*.json"]) if artifacts_dir.is_dir() else 0,
        "input_json_total": count_files(inputs_dir, ["*.json"]) if inputs_dir.is_dir() else 0,
    }
    for key, dirname in DETAIL_DIRS.items():
        counts[key] = count_files(artifacts_dir / dirname, ["*.json"]) if (artifacts_dir / dirname).is_dir() else 0

    return {
        "exists": True,
        "json": validate_json_tree(output_dir),
        "required_artifacts": required,
        "artifact_counts": counts,
    }


def program_status(package: dict[str, Any], output: dict[str, Any]) -> tuple[str, list[str]]:
    notes: list[str] = []
    status = "OK"

    if package["exists"]:
        if not package["has_mapa"]:
            notes.append("missing MAPA")
            status = "FAIL"
        if not package["has_controlflow"]:
            notes.append("missing controlflow")
            status = "FAIL"
        if package["copybooks"]["status"] == "missing":
            notes.append(f"missing {package['copybooks']['missing_count']} copybooks")
            if status != "FAIL":
                status = "WARN"
        elif package["copybooks"]["status"] == "none":
            notes.append("no copybooks packaged")
            if status != "FAIL":
                status = "WARN"
    else:
        notes.append("no input package")
        if status != "FAIL":
            status = "WARN"

    if not output["exists"]:
        notes.append("no pipeline output")
        status = "FAIL"
    else:
        json_state = output["json"]["valid"]
        if json_state is False:
            notes.append(f"{len(output['json']['invalid_files'])} invalid JSON files")
            status = "FAIL"
        missing_required = [key for key, present in output["required_artifacts"].items() if not present]
        if missing_required:
            notes.append("missing artifacts: " + ", ".join(missing_required[:5]))
            if len(missing_required) > 5:
                notes[-1] += f", +{len(missing_required) - 5} more"
            if status != "FAIL":
                status = "WARN"

    if not notes:
        notes.append("ready")
    return status, notes


def yn(value: Any) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "unknown"


def build_report(package_root: Path | None, out_root: Path | None) -> dict[str, Any]:
    package_dirs = discover_package_dirs(package_root)
    output_dirs = discover_output_dirs(out_root)
    programs = sorted(set(package_dirs) | set(output_dirs))

    rows: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    for program in programs:
        package = package_status(package_dirs.get(program))
        output = output_status(output_dirs.get(program))
        status, notes = program_status(package, output)
        status_counts[status] += 1
        rows.append(
            {
                "program": program,
                "status": status,
                "has_mapa": package["has_mapa"],
                "has_controlflow": package["has_controlflow"],
                "copybooks": package["copybooks"],
                "json": output["json"],
                "required_artifacts": output["required_artifacts"],
                "artifact_counts": output["artifact_counts"],
                "notes": notes,
            }
        )

    return {
        "package_root": str(package_root) if package_root else None,
        "out_root": str(out_root) if out_root else None,
        "summary": {
            "program_count": len(programs),
            "ok": status_counts["OK"],
            "warn": status_counts["WARN"],
            "fail": status_counts["FAIL"],
        },
        "programs": rows,
    }


def copybook_cell(row: dict[str, Any]) -> str:
    copybooks = row["copybooks"]
    missing = copybooks.get("missing_count")
    present = copybooks.get("present_count")
    if copybooks.get("status") == "complete":
        return f"complete ({present})"
    if copybooks.get("status") == "missing":
        names = ", ".join(copybooks.get("missing", [])[:3])
        extra = max(0, (missing or 0) - 3)
        if extra:
            names += f", +{extra}"
        return f"{present} present / {missing} missing: {names}"
    if copybooks.get("status") == "none":
        return "none"
    return "unknown"


def artifact_cell(row: dict[str, Any]) -> str:
    required = row["required_artifacts"]
    if not required:
        return "none"
    present = sum(1 for value in required.values() if value)
    return f"{present}/{len(required)}"


def detail_cell(row: dict[str, Any]) -> str:
    counts = row["artifact_counts"]
    if not counts:
        return "none"
    useful = [
        ("vars", counts.get("dataflow_variable", 0)),
        ("rules", counts.get("business_rule", 0)),
        ("calls", counts.get("architecture_call", 0)),
        ("comments", counts.get("program_comments_detail", 0)),
    ]
    return ", ".join(f"{name}={count}" for name, count in useful)


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# RAG Pipeline Validation",
        "",
        f"- Programs: {report['summary']['program_count']}",
        f"- OK: {report['summary']['ok']}",
        f"- WARN: {report['summary']['warn']}",
        f"- FAIL: {report['summary']['fail']}",
        "",
        "| Program | Status | MAPA | Controlflow | Copybooks | JSON | Required Artifacts | Detail Counts | Notes |",
        "|---|---|---|---|---|---|---:|---|---|",
    ]
    for row in report["programs"]:
        json_status = "unknown"
        if row["json"]["valid"] is True:
            json_status = f"ok ({row['json']['files_checked']})"
        elif row["json"]["valid"] is False:
            json_status = f"bad ({len(row['json']['invalid_files'])})"
        notes = "; ".join(row["notes"])
        lines.append(
            "| {program} | {status} | {mapa} | {cfg} | {copybooks} | {json_status} | {artifacts} | {details} | {notes} |".format(
                program=row["program"],
                status=row["status"],
                mapa=yn(row["has_mapa"]),
                cfg=yn(row["has_controlflow"]),
                copybooks=copybook_cell(row),
                json_status=json_status,
                artifacts=artifact_cell(row),
                details=detail_cell(row),
                notes=notes,
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    if not args.package_root and not args.out_root:
        raise SystemExit("Provide --package-root, --out-root, or both.")

    report = build_report(args.package_root, args.out_root)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "rag_validation_report.json"
    md_path = args.output_dir / "rag_validation_report.md"
    save_json(json_path, report)
    write_markdown(report, md_path)

    print(
        "[OK] Validation report: "
        f"{report['summary']['program_count']} programs, "
        f"{report['summary']['ok']} OK, "
        f"{report['summary']['warn']} WARN, "
        f"{report['summary']['fail']} FAIL"
    )
    print(f"[OK] JSON: {json_path}")
    print(f"[OK] Markdown: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
