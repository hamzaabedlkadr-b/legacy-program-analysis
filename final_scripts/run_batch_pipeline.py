#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, List


PROGRAM_ID_RE = re.compile(r"PROGRAM-ID\.\s*([A-Z0-9-]+)\.", re.IGNORECASE)


def parse_program_id(path: Path) -> Optional[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    m = PROGRAM_ID_RE.search(text)
    return m.group(1).upper() if m else None


def find_pdc_json(pdc_dir: Path, program: str, stem: str, pattern: str) -> Optional[Path]:
    if pdc_dir.is_file():
        return pdc_dir

    if pattern:
        try:
            cand = pdc_dir / pattern.format(program=program, stem=stem)
            if cand.exists():
                return cand
        except Exception:
            pass

    # Fallback: case-insensitive stem/program match
    for f in pdc_dir.glob("*.json"):
        if f.stem.upper() in {program.upper(), stem.upper()}:
            return f
    return None


def expected_pdc_json(pdc_dir: Path, program: str, stem: str, pattern: str) -> Optional[Path]:
    if pdc_dir.is_file():
        return pdc_dir
    if not pattern:
        return None
    try:
        return pdc_dir / pattern.format(program=program, stem=stem)
    except Exception:
        return None


def sanitize_token(x: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", (x or "").strip()).strip("_")


def make_suffix(source_tag: str, file_stem: str) -> str:
    tag = sanitize_token(source_tag)
    stem = sanitize_token(file_stem)
    if tag and stem:
        return f".{tag}.{stem}"
    if stem:
        return f".{stem}"
    if tag:
        return f".{tag}"
    return ""


def find_mapa_result(
    mapa_dir: Path,
    program: str,
    stem: str,
    program_id: Optional[str],
    pattern: str,
) -> Optional[Path]:
    if not mapa_dir.exists() or not mapa_dir.is_dir():
        return None

    if pattern:
        try:
            cand = mapa_dir / pattern.format(program=program, stem=stem)
            if cand.exists():
                return cand
            if program_id and program_id != program:
                cand = mapa_dir / pattern.format(program=program_id, stem=stem)
                if cand.exists():
                    return cand
        except Exception:
            pass

    wanted = {program, stem}
    if program_id:
        wanted.add(program_id)
    wanted = {w.upper() for w in wanted if w}
    wanted |= {f"{w}_RESULT" for w in wanted}
    for f in mapa_dir.glob("*.txt"):
        if f.stem.upper() in wanted:
            return f
    return None


def run_cmd(cmd: List[str], cwd: Optional[Path] = None, allow_fail: bool = False) -> None:
    print(">>", " ".join(str(c) for c in cmd))
    res = subprocess.run(cmd, cwd=str(cwd) if cwd else None)
    if res.returncode != 0:
        if allow_fail:
            print(f"[WARN] Command failed (continuing): {' '.join(str(c) for c in cmd)}")
            return
        raise SystemExit(res.returncode)


def collect_files(root: Path, patterns: List[str]) -> List[Path]:
    files: List[Path] = []
    seen = set()
    for pat in patterns:
        for path in sorted(root.glob(pat)):
            key = str(path.resolve()).upper()
            if key in seen:
                continue
            seen.add(key)
            files.append(path)
    return files


def main():
    ap = argparse.ArgumentParser(description="Batch pipeline for COBOL -> RAG artifacts")
    ap.add_argument("--cobol-dir", required=True, help="Folder containing COBOL .CBL files")
    ap.add_argument("--copy-dir", required=True, help="Folder containing COPYBOOK .cpy files")
    ap.add_argument("--pdc-json-dir", required=True, help="Folder containing pdc.json files (per program)")
    ap.add_argument("--pdc-json-pattern", default="{stem}.json",
                    help="Filename pattern for pdc.json (use {stem} or {program})")
    ap.add_argument("--mapa-result",
                    help="MAPA result.txt file (legacy). If omitted, use --mapa-batch-dir and --mapa-cics-dir.")
    ap.add_argument("--mapa-batch-dir", help="Folder with batch MAPA result.txt files (e.g. PDCBVC_result.txt)")
    ap.add_argument("--mapa-cics-dir", help="Folder with CICS MAPA result.txt files (e.g. PDCBVC_result.txt)")
    ap.add_argument("--mapa-result-pattern", default="{program}_result.txt",
                    help="Filename pattern inside MAPA dirs (use {program} or {stem})")
    ap.add_argument("--jcl-dir", help="Optional folder containing JCL files to analyze")
    ap.add_argument("--script3", default="script3.py", help="Path to script3.py")
    ap.add_argument("--out-root", required=True, help="Output root folder")
    ap.add_argument("--use-program-id", action="store_true",
                    help="Use PROGRAM-ID as program name (default uses file stem)")
    args = ap.parse_args()

    cobol_dir = Path(args.cobol_dir)
    copy_dir = Path(args.copy_dir)
    pdc_dir = Path(args.pdc_json_dir)
    jcl_dir = Path(args.jcl_dir) if args.jcl_dir else None
    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    global_dir = out_root / "_global"
    programs_dir = out_root / "programs"
    global_dir.mkdir(parents=True, exist_ok=True)
    programs_dir.mkdir(parents=True, exist_ok=True)

    if not cobol_dir.exists():
        raise SystemExit(f"COBOL dir not found: {cobol_dir}")
    if not copy_dir.exists():
        raise SystemExit(f"Copybook dir not found: {copy_dir}")
    if not pdc_dir.exists():
        raise SystemExit(f"pdc.json dir not found: {pdc_dir}")
    if jcl_dir and not jcl_dir.exists():
        raise SystemExit(f"JCL dir not found: {jcl_dir}")
    if jcl_dir and not jcl_dir.is_dir():
        raise SystemExit(f"JCL path is not a directory: {jcl_dir}")

    python = sys.executable
    script3 = Path(args.script3)
    if not script3.exists():
        raise SystemExit(f"script3.py not found: {script3}")
    if not script3.is_file():
        raise SystemExit(f"script3.py path is not a file: {script3}")
    jcl_builder = Path("final_scripts/jcl/build_jcl_artifacts.py")
    if jcl_dir and not jcl_builder.exists():
        raise SystemExit(f"JCL builder not found: {jcl_builder}")

    mapa_sources = []
    mapa_rag_global = None
    if args.mapa_result:
        mapa_input = Path(args.mapa_result)
        if not mapa_input.exists():
            raise SystemExit(f"MAPA result file not found: {mapa_input}")
        if not mapa_input.is_file():
            raise SystemExit(f"MAPA result is not a file: {mapa_input}")
        mapa_rag_global = global_dir / "mapa_rag_documents.json"
        run_cmd([python, str(script3), "--input", str(mapa_input), "--output", str(mapa_rag_global), "--format", "json"])
    else:
        if not args.mapa_batch_dir or not args.mapa_cics_dir:
            raise SystemExit("Provide --mapa-result or both --mapa-batch-dir and --mapa-cics-dir")
        mapa_sources = [
            ("batch", Path(args.mapa_batch_dir)),
            ("cics", Path(args.mapa_cics_dir)),
        ]
        for tag, d in mapa_sources:
            if not d.exists():
                raise SystemExit(f"MAPA dir not found: {d}")
            if not d.is_dir():
                raise SystemExit(f"MAPA path is not a directory: {d}")

    if jcl_dir:
        jcl_files = collect_files(jcl_dir, ["*.JCL", "*.jcl"])
        if not jcl_files:
            print(f"[WARN] No JCL files found in: {jcl_dir}")
        else:
            jcl_global_dir = global_dir / "jcl"
            jcl_global_dir.mkdir(parents=True, exist_ok=True)
            for jcl in jcl_files:
                run_cmd([
                    python, str(jcl_builder),
                    "--jcl", str(jcl),
                    "--output-dir", str(jcl_global_dir / jcl.stem.upper()),
                ])

    # 1) Collect COBOL programs
    cobol_files = collect_files(cobol_dir, ["*.CBL", "*.cbl", "*.COB", "*.cob"])

    if not cobol_files:
        raise SystemExit(f"No COBOL files found in: {cobol_dir}")

    program_infos = []
    missing_pdc: List[str] = []
    missing_mapa: List[str] = []
    missing_either: List[str] = []
    processed_programs: List[str] = []

    for cobol in cobol_files:
        stem = cobol.stem.upper()
        program_id = parse_program_id(cobol)
        program = program_id if (args.use_program_id and program_id) else stem

        if program_id and program_id != stem:
            print(f"[WARN] PROGRAM-ID {program_id} differs from filename {stem} for {cobol.name}")
        program_infos.append((cobol, stem, program_id, program))

    # 2) Iterate COBOL programs
    for cobol, stem, program_id, program in program_infos:
        pdc_json = find_pdc_json(pdc_dir, program=program, stem=stem, pattern=args.pdc_json_pattern)
        if not pdc_json:
            expected = expected_pdc_json(pdc_dir, program=program, stem=stem, pattern=args.pdc_json_pattern)
            expected_txt = f" expected={expected}" if expected else ""
            msg = f"{program} ({cobol.name}) missing pdc JSON.{expected_txt}"
            print(f"[WARN] {msg}; skipping")
            missing_pdc.append(msg)
            missing_either.append(msg)
            continue

        prog_root = programs_dir / program
        inputs_dir = prog_root / "inputs"
        artifacts_dir = prog_root / "artifacts"
        inputs_dir.mkdir(parents=True, exist_ok=True)
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        pdc_typed = inputs_dir / "pdc_typed.json"
        pdc_enriched = inputs_dir / "pdc_enriched.json"
        pdc_dataflow = inputs_dir / "pdc_dataflow.json"
        pdc_var_used = inputs_dir / "pdc_var_index_used.json"
        pdc_rules = inputs_dir / "pdc_rules.json"
        rag_rules = inputs_dir / "rag_documents.json"

        controlflow_cfg = artifacts_dir / "controlflow.cfg.json"

        # pdc_json -> pdc_typed + pdc_enriched
        run_cmd([
            python, "improvments/enrich_graph.py",
            "--graph", str(pdc_json),
            "--cobol", str(cobol),
            "--out", str(pdc_enriched),
            "--typed-out", str(pdc_typed),
        ])

        # pdc_enriched -> controlflow.cfg
        run_cmd([
            python, "final_scripts/controlflow.cfg/build_controlflow_cfg.py",
            "--input", str(pdc_enriched),
            "--output", str(controlflow_cfg),
        ])

        # pdc_enriched -> pdc_dataflow -> pdc_var_index_used
        run_cmd([
            python, "extract_dataflow.py",
            "--cobol", str(cobol),
            "--cfg", str(controlflow_cfg),
            "--copy-dir", str(copy_dir),
            "--out", str(pdc_dataflow),
        ])
        run_cmd([
            python, "filter_used_variables.py",
            "--in", str(pdc_dataflow),
            "--out", str(pdc_var_used),
        ])

        # pdc_rules -> rag_documents (business rules)
        run_cmd([
            python, "extract_pdc_rules.py",
            "--input", str(pdc_enriched),
            "--output", str(pdc_rules),
            "--program", program,
        ])
        run_cmd([
            python, "generate_rag_documents.py",
            "--input", str(pdc_rules),
            "--output", str(rag_rules),
        ])

        # 11 artifacts
        # MAPA-derived (per result file if using batch/cics dirs)
        mapa_inputs: List[tuple] = []
        if mapa_rag_global:
            mapa_inputs.append((mapa_rag_global, ""))
        else:
            for tag, d in mapa_sources:
                mapa_result = find_mapa_result(
                    d, program=program, stem=stem, program_id=program_id, pattern=args.mapa_result_pattern
                )
                if not mapa_result:
                    continue
                suffix = make_suffix(tag, mapa_result.stem)
                mapa_rag = artifacts_dir / f"mapa_rag_documents{suffix}.json"
                run_cmd([
                    python, str(script3),
                    "--input", str(mapa_result),
                    "--output", str(mapa_rag),
                    "--format", "json",
                ])
                mapa_inputs.append((mapa_rag, suffix))

            if not mapa_inputs:
                msg = (
                    f"{program} ({cobol.name}) missing MAPA result in "
                    f"batch={mapa_sources[0][1]} and cics={mapa_sources[1][1]} "
                    f"(pattern={args.mapa_result_pattern})"
                )
                print(f"[WARN] {msg}; skipping MAPA-derived artifacts")
                missing_mapa.append(msg)
                missing_either.append(msg)

        for mapa_rag, suffix in mapa_inputs:
            run_cmd([
                python, "final_scripts/program_summary/build_program_summary.py",
                "--input", str(mapa_rag),
                "--program", program,
                "--output", str(artifacts_dir / f"program.summary{suffix}.json"),
            ])
            run_cmd([
                python, "final_scripts/architecture.copybooks/build_architecture_copybooks.py",
                "--input", str(mapa_rag),
                "--program", program,
                "--output", str(artifacts_dir / f"architecture.copybooks{suffix}.json"),
            ])
            run_cmd([
                python, "final_scripts/architecture.calls/build_architecture_calls.py",
                "--input", str(mapa_rag),
                "--program", program,
                "--output", str(artifacts_dir / f"architecture.calls{suffix}.json"),
            ], allow_fail=True)
            run_cmd([
                python, "final_scripts/architecture.call/build_architecture_call_details.py",
                "--input", str(mapa_rag),
                "--program", program,
                "--out-dir", str(artifacts_dir / f"architecture.call{suffix}"),
            ], allow_fail=True)
            run_cmd([
                python, "final_scripts/architecture.sqlinclude/build_architecture_sqlinclude_details.py",
                "--input", str(mapa_rag),
                "--program", program,
                "--out-dir", str(artifacts_dir / f"architecture.sqlinclude{suffix}"),
            ], allow_fail=True)
            run_cmd([
                python, "final_scripts/architecture.db2_table/build_architecture_db2_table_details.py",
                "--input", str(mapa_rag),
                "--program", program,
                "--out-dir", str(artifacts_dir / f"architecture.db2_table{suffix}"),
            ], allow_fail=True)

        # Derived
        run_cmd([
            python, "final_scripts/dataflow.used_variables/build_dataflow_used_variables.py",
            "--input", str(pdc_var_used),
            "--output", str(artifacts_dir / "dataflow.used_variables.json"),
        ])
        run_cmd([
            python, "final_scripts/dataflow.variable/build_dataflow_variable_details.py",
            "--input", str(pdc_var_used),
            "--program", program,
            "--out-dir", str(artifacts_dir / "dataflow.variable"),
        ])
        run_cmd([
            python, "final_scripts/business_rule/build_business_rule_details.py",
            "--input", str(pdc_rules),
            "--program", program,
            "--out-dir", str(artifacts_dir / "business_rule"),
        ])
        run_cmd([
            python, "final_scripts/ui.cics.navigation/build_ui_cics_navigation.py",
            "--cobol", str(cobol),
            "--enriched", str(pdc_enriched),
            "--program", program,
            "--out", str(artifacts_dir / "ui.cics.navigation.json"),
        ])
        run_cmd([
            python, "final_scripts/program.comments/build_program_comments.py",
            "--cobol", str(cobol),
            "--program", program,
            "--rules", str(pdc_rules),
            "--var-index", str(pdc_var_used),
            "--rag-docs-dir", str(artifacts_dir / "program.comments"),
            "--output", str(artifacts_dir / "program.comments.json"),
        ])

        processed_programs.append(program)
        print(f"[OK] Finished program: {program} -> {prog_root}")

    print("\n=== Debug Summary ===")
    print(f"[INFO] COBOL files discovered: {len(program_infos)}")
    print(f"[INFO] Programs processed: {len(processed_programs)}")
    print(f"[INFO] Missing pdc JSON: {len(missing_pdc)}")
    print(f"[INFO] Missing MAPA result: {len(missing_mapa)}")
    print(f"[INFO] Missing either input: {len(missing_either)}")

    if missing_pdc:
        print("[DEBUG] Programs missing pdc JSON:")
        for item in missing_pdc:
            print(f"  - {item}")

    if missing_mapa:
        print("[DEBUG] Programs missing MAPA result:")
        for item in missing_mapa:
            print(f"  - {item}")


if __name__ == "__main__":
    main()
