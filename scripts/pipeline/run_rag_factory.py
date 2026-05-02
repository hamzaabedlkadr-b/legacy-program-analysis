#!/usr/bin/env python3
"""Run the full RAG document factory as one command."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = PROJECT_ROOT / "scripts" / "pipeline"
DEFAULT_PACKAGE_ROOT = Path("artifacts/final/final_scripts/input/program_packages")
DEFAULT_OUTPUT_ROOT = Path("artifacts/final/final_scripts/output/program_artifacts")
DEFAULT_RAG_INDEX_DIR = Path("artifacts/final/final_scripts/output/rag_index")
DEFAULT_VALIDATION_DIR = Path("artifacts/final/final_scripts/output/validation")
DEFAULT_FACTORY_REPORT_DIR = Path("artifacts/final/final_scripts/output/factory_report")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the COBOL RAG document factory end to end.")

    parser.add_argument("--cbl-dir", type=Path, help="Folder with .CBL/.COB files. Enables packaging stage.")
    parser.add_argument("--cpy-dir", type=Path, help="Folder with copybooks. Enables packaging stage.")
    parser.add_argument("--jcl-dir", type=Path, help="Optional folder with JCL files.")
    parser.add_argument("--mapa-dir", type=Path, help="Folder with MAPA .csv/.txt result files. Enables packaging stage.")
    parser.add_argument("--controlflow-dir", type=Path, help="Folder with control-flow JSON files. Enables packaging stage.")
    parser.add_argument("--package-root", type=Path, default=DEFAULT_PACKAGE_ROOT, help="Per-program package root.")
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUTPUT_ROOT, help="Per-program pipeline output root.")
    parser.add_argument("--rag-index-dir", type=Path, default=DEFAULT_RAG_INDEX_DIR, help="Final RAG index output folder.")
    parser.add_argument("--validation-dir", type=Path, default=DEFAULT_VALIDATION_DIR, help="Validation report output folder.")
    parser.add_argument("--factory-report-dir", type=Path, default=DEFAULT_FACTORY_REPORT_DIR, help="Factory summary output folder.")

    parser.add_argument("--copy-mode", choices=("referenced", "all"), default="referenced")
    parser.add_argument("--recursive", action="store_true", help="Search input folders recursively during packaging.")
    parser.add_argument("--use-program-id", action="store_true", help="Use PROGRAM-ID in run_batch_pipeline.py.")
    parser.add_argument("--max-text-chars", type=int, default=12000, help="Maximum indexed text chunk size.")
    parser.add_argument("--overlap-chars", type=int, default=600, help="Indexed text chunk overlap.")

    parser.add_argument("--skip-package", action="store_true", help="Do not run package_program_inputs.py.")
    parser.add_argument("--skip-pipeline", action="store_true", help="Do not run run_batch_pipeline.py.")
    parser.add_argument("--skip-index", action="store_true", help="Do not run build_rag_index.py.")
    parser.add_argument("--skip-validation", action="store_true", help="Do not run validate_rag_pipeline.py.")
    parser.add_argument(
        "--fail-on-validation-fail",
        action="store_true",
        help="Exit non-zero when the validation report contains FAIL programs or an invalid index.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def run_cmd(label: str, cmd: list[str]) -> dict[str, Any]:
    print(f"\n=== {label} ===", flush=True)
    print(">>", " ".join(str(part) for part in cmd), flush=True)
    subprocess.run(cmd, cwd=str(PROJECT_ROOT), check=True)
    return {"stage": label, "status": "ran", "command": [str(part) for part in cmd]}


def packaging_inputs_supplied(args: argparse.Namespace) -> bool:
    return any([args.cbl_dir, args.cpy_dir, args.mapa_dir, args.controlflow_dir])


def validate_packaging_args(args: argparse.Namespace) -> None:
    required = {
        "--cbl-dir": args.cbl_dir,
        "--cpy-dir": args.cpy_dir,
        "--mapa-dir": args.mapa_dir,
        "--controlflow-dir": args.controlflow_dir,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise SystemExit("Packaging stage needs: " + ", ".join(missing))


def build_stage_commands(args: argparse.Namespace) -> list[tuple[str, list[str]]]:
    python = sys.executable
    commands: list[tuple[str, list[str]]] = []

    if not args.skip_package:
        if packaging_inputs_supplied(args):
            validate_packaging_args(args)
            package_cmd = [
                python,
                str(PIPELINE_DIR / "package_program_inputs.py"),
                "--cbl-dir",
                str(args.cbl_dir),
                "--cpy-dir",
                str(args.cpy_dir),
                "--mapa-dir",
                str(args.mapa_dir),
                "--controlflow-dir",
                str(args.controlflow_dir),
                "--out-dir",
                str(args.package_root),
                "--copy-mode",
                args.copy_mode,
            ]
            if args.jcl_dir:
                package_cmd.extend(["--jcl-dir", str(args.jcl_dir)])
            if args.recursive:
                package_cmd.append("--recursive")
            commands.append(("package inputs", package_cmd))
        elif not args.package_root.exists():
            raise SystemExit(
                f"Package root does not exist and packaging inputs were not supplied: {args.package_root}"
            )

    if not args.skip_pipeline:
        pipeline_cmd = [
            python,
            str(PIPELINE_DIR / "run_batch_pipeline.py"),
            "--package-root",
            str(args.package_root),
            "--out-root",
            str(args.out_root),
        ]
        if args.use_program_id:
            pipeline_cmd.append("--use-program-id")
        commands.append(("generate program artifacts", pipeline_cmd))

    if not args.skip_index:
        commands.append(
            (
                "build RAG index",
                [
                    python,
                    str(PIPELINE_DIR / "build_rag_index.py"),
                    "--out-root",
                    str(args.out_root),
                    "--out-dir",
                    str(args.rag_index_dir),
                    "--max-text-chars",
                    str(args.max_text_chars),
                    "--overlap-chars",
                    str(args.overlap_chars),
                ],
            )
        )

    if not args.skip_validation:
        validation_cmd = [
            python,
            str(PIPELINE_DIR / "validate_rag_pipeline.py"),
            "--package-root",
            str(args.package_root),
            "--out-root",
            str(args.out_root),
            "--output-dir",
            str(args.validation_dir),
        ]
        if not args.skip_index:
            validation_cmd.extend(["--rag-index-dir", str(args.rag_index_dir)])
        elif args.rag_index_dir.exists():
            validation_cmd.extend(["--rag-index-dir", str(args.rag_index_dir)])
        commands.append(("validate factory output", validation_cmd))

    return commands


def load_optional(path: Path) -> Any:
    if not path.is_file():
        return None
    try:
        return load_json(path)
    except Exception as exc:
        return {"error": str(exc), "path": str(path)}


def factory_readiness(validation: dict[str, Any] | None) -> str:
    if not validation:
        return "UNKNOWN"
    summary = validation.get("summary") or {}
    index = validation.get("rag_index") or {}
    if summary.get("fail", 0) > 0:
        return "NOT_READY"
    if index.get("checked") and not index.get("valid"):
        return "NOT_READY"
    if summary.get("warn", 0) > 0:
        return "READY_WITH_WARNINGS"
    return "READY"


def next_actions(validation: dict[str, Any] | None) -> list[str]:
    if not validation:
        return ["Run validation to confirm package/output/index quality."]
    actions: list[str] = []
    top_reasons = (validation.get("summary") or {}).get("top_reasons") or {}
    for reason, count in top_reasons.items():
        actions.append(f"{reason}: {count} program(s)")
    index = validation.get("rag_index") or {}
    if index.get("checked") and not index.get("valid"):
        actions.append("Fix RAG index issues: " + "; ".join(index.get("notes", [])))
    if not actions:
        actions.append("Factory output is ready for vector DB ingestion.")
    return actions


def write_factory_report(args: argparse.Namespace, stages: list[dict[str, Any]]) -> dict[str, Any]:
    validation_path = args.validation_dir / "rag_validation_report.json"
    rag_manifest_path = args.rag_index_dir / "rag_manifest.json"
    package_summary_path = args.package_root / "package_summary.json"

    validation = load_optional(validation_path)
    rag_manifest = load_optional(rag_manifest_path)
    package_summary = load_optional(package_summary_path)
    readiness = factory_readiness(validation if isinstance(validation, dict) else None)

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "readiness": readiness,
        "paths": {
            "package_root": str(args.package_root),
            "out_root": str(args.out_root),
            "rag_index_dir": str(args.rag_index_dir),
            "validation_dir": str(args.validation_dir),
            "factory_report_dir": str(args.factory_report_dir),
        },
        "stages": stages,
        "package_summary": package_summary,
        "validation_summary": (validation or {}).get("summary") if isinstance(validation, dict) else None,
        "rag_index_summary": {
            "program_count": (rag_manifest or {}).get("program_count") if isinstance(rag_manifest, dict) else None,
            "indexed_documents": (rag_manifest or {}).get("indexed_documents") if isinstance(rag_manifest, dict) else None,
            "source_documents": (rag_manifest or {}).get("source_documents") if isinstance(rag_manifest, dict) else None,
            "invalid_files": len((rag_manifest or {}).get("invalid_files") or []) if isinstance(rag_manifest, dict) else None,
        },
        "next_actions": next_actions(validation if isinstance(validation, dict) else None),
    }

    args.factory_report_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.factory_report_dir / "rag_factory_report.json"
    md_path = args.factory_report_dir / "rag_factory_report.md"
    save_json(json_path, report)

    lines = [
        "# RAG Factory Report",
        "",
        f"- Readiness: {report['readiness']}",
        f"- Package root: {args.package_root}",
        f"- Program output: {args.out_root}",
        f"- RAG index: {args.rag_index_dir}",
        f"- Validation: {args.validation_dir}",
        "",
        "## Summary",
    ]
    validation_summary = report.get("validation_summary") or {}
    if validation_summary:
        lines.extend(
            [
                f"- Programs: {validation_summary.get('program_count', 0)}",
                f"- OK: {validation_summary.get('ok', 0)}",
                f"- WARN: {validation_summary.get('warn', 0)}",
                f"- FAIL: {validation_summary.get('fail', 0)}",
            ]
        )
    index_summary = report.get("rag_index_summary") or {}
    if index_summary:
        lines.extend(
            [
                f"- Indexed documents/chunks: {index_summary.get('indexed_documents')}",
                f"- Source documents: {index_summary.get('source_documents')}",
                f"- Index invalid files: {index_summary.get('invalid_files')}",
            ]
        )
    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {action}" for action in report["next_actions"])
    lines.extend(["", "## Stage Commands"])
    for stage in stages:
        lines.append(f"- {stage['stage']}: {stage['status']}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\n[OK] Factory report: {json_path}", flush=True)
    print(f"[OK] Factory summary: {md_path}", flush=True)
    print(f"[OK] Readiness: {readiness}", flush=True)
    return report


def main() -> int:
    args = parse_args()
    commands = build_stage_commands(args)
    stages: list[dict[str, Any]] = []
    for label, cmd in commands:
        stages.append(run_cmd(label, cmd))

    report = write_factory_report(args, stages)
    if args.fail_on_validation_fail and report["readiness"] == "NOT_READY":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
