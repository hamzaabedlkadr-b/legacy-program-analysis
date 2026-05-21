#!/usr/bin/env python3
"""Run a program test case through the analysis and combined pipelines.

This is a convenience wrapper for thesis/demo testing. It keeps outputs under
artifacts/experiments/<PROGRAM>/ so stable artifacts are not overwritten.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = PROJECT_ROOT / "scripts" / "pipeline"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program", required=True, help="Program name, for example PDCBVC or NEWPROG.")
    parser.add_argument("--mode", choices=("my", "combined", "both"), default="both")
    parser.add_argument("--case-root", type=Path, help="Folder containing cbl/cobol, copybooks, mapa, controlflow, and optional jcl folders.")
    parser.add_argument("--cbl-dir", type=Path, help="Folder with .CBL/.COB files.")
    parser.add_argument("--cpy-dir", type=Path, help="Folder with copybooks.")
    parser.add_argument("--mapa-dir", type=Path, help="Folder with MAPA result files.")
    parser.add_argument("--controlflow-dir", type=Path, help="Folder with control-flow JSON files.")
    parser.add_argument("--jcl-dir", type=Path, help="Optional folder with JCL files.")
    parser.add_argument("--cobol-rekt-rag-bundle", type=Path, help="Friend's cobol-rekt knowledge-base_rag bundle for combined mode.")
    parser.add_argument("--source-label", help="Portable label for the cobol-rekt bundle in provenance.")
    parser.add_argument("--out-base", type=Path, default=Path("artifacts/experiments"), help="Experiment output base folder.")
    parser.add_argument("--copy-mode", choices=("referenced", "all"), default="referenced")
    parser.add_argument("--recursive", action="store_true", help="Search input folders recursively.")
    parser.add_argument("--use-program-id", action="store_true", help="Pass --use-program-id to run_rag_factory.py.")
    parser.add_argument("--optimize-constants", action="store_true", help="Pass --optimize-constants to run_rag_factory.py.")
    parser.add_argument(
        "--rag-profile",
        choices=("full", "compact"),
        default="full",
        help="RAG indexing profile to pass to run_rag_factory.py.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def resolve_path(path: Path | None) -> Path | None:
    if path is None:
        return None
    path = path.expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def first_existing(case_root: Path | None, names: tuple[str, ...]) -> Path | None:
    if case_root is None:
        return None
    for name in names:
        candidate = case_root / name
        if candidate.exists():
            return candidate.resolve()
    return None


def input_paths(args: argparse.Namespace) -> dict[str, Path | None]:
    case_root = resolve_path(args.case_root)
    return {
        "cbl_dir": resolve_path(args.cbl_dir) or first_existing(case_root, ("cbl", "cobol", "src")),
        "cpy_dir": resolve_path(args.cpy_dir) or first_existing(case_root, ("copybooks", "cpy", "copy")),
        "mapa_dir": resolve_path(args.mapa_dir) or first_existing(case_root, ("mapa", "map", "mapa_results")),
        "controlflow_dir": resolve_path(args.controlflow_dir) or first_existing(case_root, ("controlflow", "cfg", "control_flow")),
        "jcl_dir": resolve_path(args.jcl_dir) or first_existing(case_root, ("jcl", "jobs")),
        "rekt_bundle": resolve_path(args.cobol_rekt_rag_bundle) or first_existing(case_root, ("knowledge-base_rag", "knowledge_base_rag", "cobol_rekt")),
    }


def require_dir(label: str, path: Path | None) -> Path:
    if path is None:
        raise SystemExit(f"Missing {label}. Pass --{label.replace('_', '-')} or use --case-root with a matching folder.")
    if not path.exists():
        raise SystemExit(f"{label} does not exist: {path}")
    if not path.is_dir():
        raise SystemExit(f"{label} must be a directory: {path}")
    return path


def run(label: str, cmd: list[str], dry_run: bool) -> dict[str, Any]:
    print(f"\n=== {label} ===", flush=True)
    print(" ".join(cmd), flush=True)
    if not dry_run:
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)
    return {"label": label, "command": cmd, "status": "planned" if dry_run else "ran"}


def find_artifacts_root(programs_root: Path, program: str) -> Path:
    expected = programs_root / program / "artifacts"
    if expected.exists():
        return expected.resolve()
    candidates = sorted(programs_root.glob("*/artifacts"))
    if len(candidates) == 1:
        return candidates[0].resolve()
    return expected.resolve()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    args = parse_args()
    program = args.program.upper()
    paths = input_paths(args)
    out_base = resolve_path(args.out_base) or (PROJECT_ROOT / "artifacts" / "experiments")
    exp_root = out_base / program

    my_root = exp_root / "my_analysis"
    package_root = my_root / "packages"
    program_artifacts_root = my_root / "program_artifacts"
    rag_index_dir = my_root / "rag_index"
    validation_dir = my_root / "validation"
    factory_report_dir = my_root / "factory_report"
    programs_root = program_artifacts_root / "programs"
    my_final_scripts_root = find_artifacts_root(programs_root, program)
    my_rag_jsonl = (rag_index_dir / "rag_documents.jsonl").resolve()

    combined_root = exp_root / "combined"
    combined_final_scripts_root = (combined_root / "final_scripts").resolve()
    combined_rag_jsonl = (combined_root / "rag_index" / f"{program}_combined.jsonl").resolve()

    stages: list[dict[str, Any]] = []

    if args.mode in {"my", "both"}:
        cbl_dir = require_dir("cbl_dir", paths["cbl_dir"])
        cpy_dir = require_dir("cpy_dir", paths["cpy_dir"])
        mapa_dir = require_dir("mapa_dir", paths["mapa_dir"])
        controlflow_dir = require_dir("controlflow_dir", paths["controlflow_dir"])
        jcl_dir = paths["jcl_dir"] if paths["jcl_dir"] and paths["jcl_dir"].exists() else None

        cmd = [
            sys.executable,
            str(PIPELINE_DIR / "run_rag_factory.py"),
            "--cbl-dir",
            str(cbl_dir),
            "--cpy-dir",
            str(cpy_dir),
            "--mapa-dir",
            str(mapa_dir),
            "--controlflow-dir",
            str(controlflow_dir),
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
            "--copy-mode",
            args.copy_mode,
            "--rag-profile",
            args.rag_profile,
        ]
        if jcl_dir:
            cmd.extend(["--jcl-dir", str(jcl_dir)])
        if args.recursive:
            cmd.append("--recursive")
        if args.use_program_id:
            cmd.append("--use-program-id")
        if args.optimize_constants:
            cmd.append("--optimize-constants")
        stages.append(run("my analysis", cmd, args.dry_run))

    if args.mode in {"combined", "both"}:
        rekt_bundle = require_dir("cobol_rekt_rag_bundle", paths["rekt_bundle"])
        if not args.dry_run:
            if not my_final_scripts_root.exists():
                raise SystemExit(f"My final_scripts-style artifact root does not exist yet: {my_final_scripts_root}")
            if not my_rag_jsonl.exists():
                raise SystemExit(f"My RAG JSONL does not exist yet: {my_rag_jsonl}")
        source_label = args.source_label or f"cobol-rekt/knowledge-base_rag/{program}"
        cmd = [
            sys.executable,
            str(PIPELINE_DIR / "import_cobol_rekt_rag_bundle.py"),
            "--program",
            program,
            "--cobol-rekt-rag-bundle",
            str(rekt_bundle),
            "--source-label",
            source_label,
            "--final-scripts-root",
            str(my_final_scripts_root),
            "--out-root",
            str(combined_final_scripts_root),
            "--base-rag-jsonl",
            str(my_rag_jsonl),
            "--combined-rag-jsonl",
            str(combined_rag_jsonl),
        ]
        stages.append(run("combined analysis", cmd, args.dry_run))

    summary = {
        "program": program,
        "mode": args.mode,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {key: str(value) if value else None for key, value in paths.items()},
        "outputs": {
            "my_final_scripts_root": str(my_final_scripts_root),
            "my_rag_jsonl": str(my_rag_jsonl),
            "combined_final_scripts_root": str(combined_final_scripts_root),
            "combined_rag_jsonl": str(combined_rag_jsonl),
            "validation_dir": str(validation_dir.resolve()),
            "factory_report_dir": str(factory_report_dir.resolve()),
        },
        "stages": stages,
    }
    summary_path = exp_root / "run_summary.json"
    write_json(summary_path, summary)

    next_steps = f"""# Next RAG commands for {program}

From the cobol-rag-pipeline repo, run one of these:

```bash
./scripts/run_rag_test.sh --mode my --program {program} --analysis-repo ../legacy-program-analysis
./scripts/run_rag_test.sh --mode combined --program {program} --analysis-repo ../legacy-program-analysis
./scripts/run_rag_test.sh --mode rekt --program {program} --rekt-bundle /path/to/knowledge-base_rag
```

Generated paths:

- My JSONL: `{my_rag_jsonl}`
- My final scripts root: `{my_final_scripts_root}`
- Combined JSONL: `{combined_rag_jsonl}`
- Combined final scripts root: `{combined_final_scripts_root}`
"""
    write_text(exp_root / "NEXT_RAG_COMMANDS.md", next_steps)

    print("\n=== Summary ===")
    print(json.dumps(summary["outputs"], indent=2))
    print(f"\nWrote: {summary_path}")
    print(f"Wrote: {exp_root / 'NEXT_RAG_COMMANDS.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
