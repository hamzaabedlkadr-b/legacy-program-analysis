#!/usr/bin/env python3
"""Run the fixed final_scripts/input layout into the RAG JSONL output.

Expected input layout:

  artifacts/final/final_scripts/input/
    PROGRAM1/
      PROGRAM1.CBL
      PROGRAM1_result.csv
      PROGRAM1_controlflow.json
      copybooks/
      jcl/                  optional
      knowledge-base_rag/   optional, for combined mode
    knowledge-base_rag/     optional shared cobol-rekt bundle for combined mode

The script writes stable generated output under:

  artifacts/final/final_scripts/output/
    program_artifacts/
    rag_index/rag_documents.jsonl
    validation/
    factory_report/

It can also create a combined output when a cobol-rekt knowledge-base_rag bundle
is present for the selected program.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = PROJECT_ROOT / "scripts" / "pipeline"
DEFAULT_INPUT_ROOT = Path("artifacts/final/final_scripts/input")
DEFAULT_OUTPUT_ROOT = Path("artifacts/final/final_scripts/output")


class ConfigError(SystemExit):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program", "-p", help="Program to run. If omitted, runs every program folder in input root.")
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT, help="Fixed input root.")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT, help="Generated output root.")
    parser.add_argument("--mode", choices=("my", "combined", "both"), default="my")
    parser.add_argument("--cobol-rekt-rag-bundle", type=Path, help="Bundle for combined mode. Use only with one --program.")
    parser.add_argument("--source-label", help="Portable source label for combined provenance.")
    parser.add_argument("--copy-mode", choices=("referenced", "all"), default="referenced")
    parser.add_argument("--recursive", action="store_true", help="Search program folders recursively.")
    parser.add_argument("--use-program-id", action="store_true", help="Pass --use-program-id to the artifact pipeline.")
    parser.add_argument("--optimize-constants", action="store_true", help="Pass --optimize-constants to the artifact pipeline.")
    parser.add_argument(
        "--rag-profile",
        choices=("full", "compact"),
        default="full",
        help="RAG indexing profile to pass to run_rag_factory.py.",
    )
    parser.add_argument("--no-clean", action="store_true", help="Do not clean generated package/output folders before running.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would run without executing.")
    return parser.parse_args()


def resolve(path: Path) -> Path:
    path = path.expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def safe_rmtree(path: Path, allowed_parent: Path) -> None:
    path = path.resolve()
    allowed_parent = allowed_parent.resolve()
    if not path.exists():
        return
    if not is_relative_to(path, allowed_parent):
        raise ConfigError(f"Refusing to delete outside {allowed_parent}: {path}")
    shutil.rmtree(path)


def load_text(path: Path) -> str:
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


DOT_EDGE_RE = re.compile(r"<([^>]+)>\s*->\s*<([^>]+)>\s*;")
DOT_DIGRAPH_RE = re.compile(r"digraph\s+([A-Za-z0-9_]+)\s*\{", re.IGNORECASE)
DOT_RANKDIR_RE = re.compile(r"rankdir\s*=\s*([A-Za-z]+)\s*;", re.IGNORECASE)


def parse_dot_controlflow(text: str) -> dict[str, Any] | None:
    match = DOT_DIGRAPH_RE.search(text)
    if not match:
        return None
    nodes: set[str] = set()
    edges: list[dict[str, str]] = []
    for source, target in DOT_EDGE_RE.findall(text):
        nodes.add(source)
        nodes.add(target)
        edges.append({"from": source, "to": target})
    if not edges:
        return None
    rank_match = DOT_RANKDIR_RE.search(text)
    return {
        "graph": {"name": match.group(1), "rankdir": rank_match.group(1) if rank_match else None},
        "nodes": sorted(nodes),
        "edges": edges,
    }


def ensure_controlflow_json(info: dict[str, Any], input_root: Path, dry_run: bool) -> Path:
    path = Path(info["controlflow"])
    try:
        with path.open("r", encoding="utf-8") as handle:
            json.load(handle)
        info["controlflow_format"] = "json"
        return path.parent
    except json.JSONDecodeError:
        pass

    text = load_text(path)
    converted = parse_dot_controlflow(text)
    if converted is None:
        raise ConfigError(f"Controlflow file is neither valid JSON nor supported DOT: {path}")

    out_dir = input_root / "_normalized_controlflow" / info["program"]
    out_path = out_dir / path.name
    info["controlflow_format"] = "dot-normalized-to-json"
    info["normalized_controlflow"] = str(out_path.resolve())
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        write_json(out_path, converted)
    return out_dir.resolve()


def program_name_from_cbl(path: Path) -> str:
    import re

    text = load_text(path)
    match = re.search(r"\bPROGRAM-ID\.\s*([A-Z0-9_-]+)", text, re.IGNORECASE)
    return (match.group(1) if match else path.stem).upper()


def first_file(root: Path, suffixes: tuple[str, ...]) -> Path | None:
    for path in sorted(root.iterdir()):
        if path.is_file() and path.suffix.lower() in suffixes:
            return path
    return None


def find_program_dirs(input_root: Path, selected_program: str | None) -> list[Path]:
    if not input_root.exists():
        raise ConfigError(f"Input root does not exist: {input_root}")
    if selected_program:
        program_dir = input_root / selected_program.upper()
        if not program_dir.exists():
            # Allow exact mixed-case folder names too.
            matches = [p for p in input_root.iterdir() if p.is_dir() and p.name.upper() == selected_program.upper()]
            if matches:
                program_dir = matches[0]
        if not program_dir.exists():
            raise ConfigError(f"Program input folder not found: {program_dir}")
        return [program_dir.resolve()]
    return sorted(
        path.resolve()
        for path in input_root.iterdir()
        if path.is_dir() and not path.name.startswith("_") and first_file(path, (".cbl", ".cob", ".cobol"))
    )


def validate_program_dir(program_dir: Path) -> dict[str, Any]:
    cbl = first_file(program_dir, (".cbl", ".cob", ".cobol"))
    if cbl is None:
        raise ConfigError(f"No COBOL source found in {program_dir}")
    program = program_name_from_cbl(cbl)
    copybooks = program_dir / "copybooks"
    if not copybooks.is_dir():
        raise ConfigError(f"Missing copybooks folder for {program}: {copybooks}")
    mapa = first_file(program_dir, (".csv", ".txt"))
    if mapa is None:
        raise ConfigError(f"Missing MAPA result .csv/.txt in {program_dir}")
    cfg_candidates = [
        p for p in sorted(program_dir.iterdir())
        if p.is_file() and p.suffix.lower() == ".json" and ("control" in p.stem.lower() or "cfg" in p.stem.lower() or p.stem.upper() == program)
    ]
    if not cfg_candidates:
        raise ConfigError(f"Missing controlflow JSON in {program_dir}")
    return {
        "program": program,
        "program_dir": str(program_dir),
        "cbl": str(cbl),
        "copybooks": str(copybooks),
        "mapa": str(mapa),
        "controlflow": str(cfg_candidates[0]),
        "jcl": str(program_dir / "jcl") if (program_dir / "jcl").is_dir() else None,
        "rekt_bundle": find_rekt_bundle(program_dir),
    }


def find_rekt_bundle(program_dir: Path) -> str | None:
    candidates = [
        program_dir / "knowledge-base_rag",
        program_dir / "knowledge-base_rag" / "knowledge-base_rag",
        program_dir / "knowledge_base_rag",
        program_dir / "cobol_rekt" / "knowledge-base_rag",
        program_dir / "cobol_rekt" / "knowledge-base_rag" / "knowledge-base_rag",
        program_dir.parent / "knowledge-base_rag",
        program_dir.parent / "knowledge-base_rag" / "knowledge-base_rag",
        program_dir.parent / "knowledge_base_rag",
    ]
    for candidate in candidates:
        if (candidate / "manifest.json").is_file() or ((candidate / "knowledge-base_rag" / "manifest.json").is_file()):
            return str(candidate.resolve())
    return None


def run(label: str, cmd: list[str], *, dry_run: bool) -> dict[str, Any]:
    print(f"\n=== {label} ===", flush=True)
    print(" ".join(cmd), flush=True)
    if not dry_run:
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)
    return {"stage": label, "command": cmd, "status": "planned" if dry_run else "ran"}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_root = resolve(args.input_root)
    output_root = resolve(args.output_root)
    package_root = input_root / "_generated_program_packages"
    program_artifacts_root = output_root / "program_artifacts"
    rag_index_dir = output_root / "rag_index"
    validation_dir = output_root / "validation"
    factory_report_dir = output_root / "factory_report"
    combined_root = output_root / "combined"

    program_dirs = find_program_dirs(input_root, args.program)
    if not program_dirs:
        raise ConfigError(f"No program folders found under {input_root}")
    programs = [validate_program_dir(program_dir) for program_dir in program_dirs]

    if args.cobol_rekt_rag_bundle and len(programs) != 1:
        raise ConfigError("--cobol-rekt-rag-bundle can only be used with one --program")

    stages: list[dict[str, Any]] = []

    if args.mode in {"my", "both"}:
        if not args.no_clean and not args.dry_run:
            safe_rmtree(package_root, input_root)
            safe_rmtree(input_root / "_normalized_controlflow", input_root)
            safe_rmtree(output_root, PROJECT_ROOT / "artifacts" / "final" / "final_scripts")

        for info in programs:
            controlflow_dir = ensure_controlflow_json(info, input_root, args.dry_run)
            cmd = [
                sys.executable,
                str(PIPELINE_DIR / "package_program_inputs.py"),
                "--cbl-dir",
                info["program_dir"],
                "--cpy-dir",
                info["copybooks"],
                "--mapa-dir",
                info["program_dir"],
                "--controlflow-dir",
                str(controlflow_dir),
                "--out-dir",
                str(package_root),
                "--copy-mode",
                args.copy_mode,
            ]
            if info["jcl"]:
                cmd.extend(["--jcl-dir", info["jcl"]])
            if args.recursive:
                cmd.append("--recursive")
            stages.append(run(f"package {info['program']}", cmd, dry_run=args.dry_run))

        cmd = [
            sys.executable,
            str(PIPELINE_DIR / "run_rag_factory.py"),
            "--skip-package",
            "--package-root",
            str(package_root),
            "--out-root",
            str(program_artifacts_root),
            "--rag-index-dir",
            str(rag_index_dir),
            "--validation-dir",
            str(validation_dir),
            "--factory-report-dir",
            str(factory_report_dir),
            "--rag-profile",
            args.rag_profile,
        ]
        if args.use_program_id:
            cmd.append("--use-program-id")
        if args.optimize_constants:
            cmd.append("--optimize-constants")
        stages.append(run("build final_scripts output and RAG JSONL", cmd, dry_run=args.dry_run))

    if args.mode in {"combined", "both"}:
        for info in programs:
            program = info["program"]
            bundle = str(resolve(args.cobol_rekt_rag_bundle)) if args.cobol_rekt_rag_bundle else info["rekt_bundle"]
            if not bundle:
                raise ConfigError(f"No knowledge-base_rag bundle found for combined mode: {program}")
            final_scripts_root = program_artifacts_root / "programs" / program / "artifacts"
            if not args.dry_run and not final_scripts_root.exists():
                raise ConfigError(f"Missing generated final_scripts-style root for {program}: {final_scripts_root}")
            base_rag_jsonl = rag_index_dir / "rag_documents.jsonl"
            combined_jsonl = combined_root / "rag_index" / f"{program}_combined.jsonl"
            source_label = args.source_label or f"cobol-rekt/knowledge-base_rag/{program}"
            cmd = [
                sys.executable,
                str(PIPELINE_DIR / "import_cobol_rekt_rag_bundle.py"),
                "--program",
                program,
                "--cobol-rekt-rag-bundle",
                bundle,
                "--source-label",
                source_label,
                "--final-scripts-root",
                str(final_scripts_root),
                "--out-root",
                str(combined_root / "final_scripts" / program),
                "--base-rag-jsonl",
                str(base_rag_jsonl),
                "--combined-rag-jsonl",
                str(combined_jsonl),
            ]
            stages.append(run(f"combined {program}", cmd, dry_run=args.dry_run))

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_root": str(input_root),
        "output_root": str(output_root),
        "mode": args.mode,
        "programs": programs,
        "outputs": {
            "rag_documents_jsonl": str((rag_index_dir / "rag_documents.jsonl").resolve()),
            "rag_documents_json": str((rag_index_dir / "rag_documents.json").resolve()),
            "program_artifacts_root": str(program_artifacts_root.resolve()),
            "validation_dir": str(validation_dir.resolve()),
            "factory_report_dir": str(factory_report_dir.resolve()),
            "combined_root": str(combined_root.resolve()),
        },
        "stages": stages,
    }
    write_json(output_root / "fixed_input_run_summary.json", summary)
    print("\n=== Outputs ===")
    print(json.dumps(summary["outputs"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
