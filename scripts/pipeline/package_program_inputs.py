#!/usr/bin/env python3
"""Create per-program input packages for the final artifact/RAG pipeline.

The packager groups COBOL source, copybooks, JCL, MAPA CSV/TXT output, and
control-flow JSON into one folder per program:

    <out-dir>/<PROGRAM>/
      cobol/
      copybooks/
      jcl/
      mapa/
      controlflow/
      manifest.json

It is intentionally conservative: it never deletes existing output, and it
records missing matches in each manifest.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


COPY_RE = re.compile(
    r"^\s*(?!\*)\s*(?:[A-Z0-9-]+\s+)?COPY\s+['\"]?([A-Z0-9_-]+)['\"]?",
    re.IGNORECASE,
)
PROGRAM_ID_RE = re.compile(r"\bPROGRAM-ID\.\s*([A-Z0-9_-]+)", re.IGNORECASE)


@dataclass
class PackageManifest:
    program: str
    source_stem: str
    files: dict[str, list[str]] = field(
        default_factory=lambda: {
            "cobol": [],
            "copybooks": [],
            "jcl": [],
            "mapa": [],
            "controlflow": [],
        }
    )
    missing: dict[str, list[str]] = field(
        default_factory=lambda: {
            "copybooks": [],
            "jcl": [],
            "mapa": [],
            "controlflow": [],
        }
    )
    notes: list[str] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create one final_scripts/input package per COBOL program."
    )
    parser.add_argument("--cbl-dir", required=True, type=Path, help="Folder with .CBL/.cbl files")
    parser.add_argument("--cpy-dir", required=True, type=Path, help="Folder with copybooks")
    parser.add_argument("--jcl-dir", type=Path, help="Optional folder with .JCL/.jcl files")
    parser.add_argument(
        "--mapa-dir",
        required=True,
        type=Path,
        help="Folder with MAPA result files, usually *_result.csv or *_result.txt",
    )
    parser.add_argument(
        "--controlflow-dir",
        required=True,
        type=Path,
        help="Folder with control-flow JSON files",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("artifacts/final/final_scripts/input/program_packages"),
        help="Destination package folder",
    )
    parser.add_argument(
        "--copy-mode",
        choices=("referenced", "all"),
        default="referenced",
        help="Copy only COPY-referenced copybooks or every file in --cpy-dir",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search input folders recursively",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned package summary without copying files",
    )
    return parser.parse_args()


def iter_files(root: Path, recursive: bool) -> Iterable[Path]:
    pattern = "**/*" if recursive else "*"
    return (p for p in root.glob(pattern) if p.is_file())


def find_cobol_files(cbl_dir: Path, recursive: bool) -> list[Path]:
    return sorted(
        p
        for p in iter_files(cbl_dir, recursive)
        if p.suffix.lower() in {".cbl", ".cob", ".cobol"}
    )


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


def program_name(cbl: Path) -> str:
    match = PROGRAM_ID_RE.search(read_text(cbl))
    return (match.group(1) if match else cbl.stem).upper()


def referenced_copybooks(cbl: Path) -> list[str]:
    names: set[str] = set()
    for line in read_text(cbl).splitlines():
        match = COPY_RE.search(line)
        if match:
            name = match.group(1).upper()
            if name not in {"DFHBMSCA", "DFHAID", "SQLCA", "SQLDA"}:
                names.add(name)
    return sorted(names)


def index_by_stem(root: Path | None, recursive: bool) -> dict[str, list[Path]]:
    if not root or not root.exists():
        return {}
    index: dict[str, list[Path]] = {}
    for path in iter_files(root, recursive):
        index.setdefault(path.stem.upper(), []).append(path)
        index.setdefault(path.name.upper(), []).append(path)
    return index


def find_copybook(name: str, cpy_index: dict[str, list[Path]]) -> Path | None:
    keys = [
        name.upper(),
        f"{name}.CPY".upper(),
        f"{name}.COPY".upper(),
        f"{name}.COB".upper(),
    ]
    for key in keys:
        matches = cpy_index.get(key)
        if matches:
            return sorted(matches)[0]
    return None


def find_mapa(program: str, stem: str, mapa_index: dict[str, list[Path]]) -> list[Path]:
    keys = [
        f"{program}_RESULT",
        f"{stem}_RESULT",
        f"{program}_RESULT.CSV",
        f"{stem}_RESULT.CSV",
        f"{program}_RESULT.TXT",
        f"{stem}_RESULT.TXT",
        program,
        stem,
    ]
    found: list[Path] = []
    for key in keys:
        for path in mapa_index.get(key.upper(), []):
            if path.suffix.lower() in {".csv", ".txt"} and path not in found:
                found.append(path)
    if not found:
        all_mapa = sorted(
            {
                path
                for paths in mapa_index.values()
                for path in paths
                if path.suffix.lower() in {".csv", ".txt"}
            }
        )
        if len(all_mapa) == 1:
            found.append(all_mapa[0])
    return sorted(found)


def find_controlflow(program: str, stem: str, cfg_index: dict[str, list[Path]]) -> list[Path]:
    keys = [
        program,
        stem,
        f"{program}_CONTROLFLOW",
        f"{stem}_CONTROLFLOW",
        f"{program}_CFG",
        f"{stem}_CFG",
        f"{program}.JSON",
        f"{stem}.JSON",
        f"{program}_CONTROLFLOW.JSON",
        f"{stem}_CONTROLFLOW.JSON",
        f"{program}_CFG.JSON",
        f"{stem}_CFG.JSON",
    ]
    found: list[Path] = []
    for key in keys:
        for path in cfg_index.get(key.upper(), []):
            if path.suffix.lower() == ".json" and path not in found:
                found.append(path)
    if not found:
        all_json = sorted(
            {
                path
                for paths in cfg_index.values()
                for path in paths
                if path.suffix.lower() == ".json"
            }
        )
        if len(all_json) == 1:
            found.append(all_json[0])
    return sorted(found)


def find_jcl(program: str, stem: str, jcl_dir: Path | None, recursive: bool) -> list[Path]:
    if not jcl_dir or not jcl_dir.exists():
        return []
    exact: list[Path] = []
    contains: list[Path] = []
    for path in iter_files(jcl_dir, recursive):
        if path.suffix.lower() not in {".jcl", ".txt"}:
            continue
        upper_stem = path.stem.upper()
        if upper_stem in {program, stem.upper()}:
            exact.append(path)
            continue
        text = read_text(path).upper()
        if program in text or stem.upper() in text:
            contains.append(path)
    return sorted(exact + [p for p in contains if p not in exact])


def copy_file(src: Path, dest_dir: Path, dry_run: bool) -> str:
    dest = dest_dir / src.name
    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    return str(dest)


def write_manifest(manifest: PackageManifest, dest: Path, dry_run: bool) -> None:
    if dry_run:
        return
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "manifest.json").write_text(
        json.dumps(manifest.__dict__, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def package_program(
    cbl: Path,
    args: argparse.Namespace,
    cpy_index: dict[str, list[Path]],
    mapa_index: dict[str, list[Path]],
    cfg_index: dict[str, list[Path]],
) -> PackageManifest:
    program = program_name(cbl)
    pkg_dir = args.out_dir / program
    manifest = PackageManifest(program=program, source_stem=cbl.stem)

    manifest.files["cobol"].append(copy_file(cbl, pkg_dir / "cobol", args.dry_run))

    if args.copy_mode == "all":
        copybooks = sorted(iter_files(args.cpy_dir, args.recursive))
    else:
        copybooks = []
        for name in referenced_copybooks(cbl):
            match = find_copybook(name, cpy_index)
            if match:
                copybooks.append(match)
            else:
                manifest.missing["copybooks"].append(name)
    for copybook in sorted(set(copybooks)):
        manifest.files["copybooks"].append(copy_file(copybook, pkg_dir / "copybooks", args.dry_run))

    jcl_files = find_jcl(program, cbl.stem, args.jcl_dir, args.recursive)
    if not jcl_files and args.jcl_dir:
        manifest.missing["jcl"].append(f"No JCL matched {program} / {cbl.stem}")
    for jcl in jcl_files:
        manifest.files["jcl"].append(copy_file(jcl, pkg_dir / "jcl", args.dry_run))

    mapa_files = find_mapa(program, cbl.stem, mapa_index)
    if not mapa_files:
        manifest.missing["mapa"].append(f"No MAPA result matched {program} / {cbl.stem}")
    for mapa in mapa_files:
        manifest.files["mapa"].append(copy_file(mapa, pkg_dir / "mapa", args.dry_run))

    cfg_files = find_controlflow(program, cbl.stem, cfg_index)
    if not cfg_files:
        manifest.missing["controlflow"].append(f"No control-flow JSON matched {program} / {cbl.stem}")
    for cfg in cfg_files:
        manifest.files["controlflow"].append(copy_file(cfg, pkg_dir / "controlflow", args.dry_run))

    if args.copy_mode == "referenced":
        manifest.notes.append("Copybooks are limited to COPY statements found directly in the COBOL source.")
    else:
        manifest.notes.append("All files from --cpy-dir were copied into this package.")

    write_manifest(manifest, pkg_dir, args.dry_run)
    return manifest


def validate_args(args: argparse.Namespace) -> None:
    for attr in ("cbl_dir", "cpy_dir", "mapa_dir", "controlflow_dir"):
        path = getattr(args, attr)
        if not path.exists() or not path.is_dir():
            raise SystemExit(f"--{attr.replace('_', '-')} is not a directory: {path}")
    if args.jcl_dir and (not args.jcl_dir.exists() or not args.jcl_dir.is_dir()):
        raise SystemExit(f"--jcl-dir is not a directory: {args.jcl_dir}")


def main() -> int:
    args = parse_args()
    validate_args(args)

    cobol_files = find_cobol_files(args.cbl_dir, args.recursive)
    if not cobol_files:
        raise SystemExit(f"No COBOL files found in {args.cbl_dir}")

    cpy_index = index_by_stem(args.cpy_dir, args.recursive)
    mapa_index = index_by_stem(args.mapa_dir, args.recursive)
    cfg_index = index_by_stem(args.controlflow_dir, args.recursive)

    if not args.dry_run:
        args.out_dir.mkdir(parents=True, exist_ok=True)

    manifests = [
        package_program(cbl, args, cpy_index, mapa_index, cfg_index)
        for cbl in cobol_files
    ]

    summary = {
        "out_dir": str(args.out_dir),
        "program_count": len(manifests),
        "programs": [
            {
                "program": m.program,
                "cobol": len(m.files["cobol"]),
                "copybooks": len(m.files["copybooks"]),
                "jcl": len(m.files["jcl"]),
                "mapa": len(m.files["mapa"]),
                "controlflow": len(m.files["controlflow"]),
                "missing": m.missing,
            }
            for m in manifests
        ],
    }

    if args.dry_run:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        summary_path = args.out_dir / "package_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Created {len(manifests)} package(s) under {args.out_dir}")
        print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
