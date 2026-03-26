import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# -----------------------------
# Config
# -----------------------------

COBOL_EXTS = {".cbl", ".cob", ".cobol"}
COPYBOOK_EXTS = {".cpy", ".copy", ".cpb"}
BMS_EXTS = {".bms"}
LISTING_EXTS = {".lst"}

DIR_CONFIG: Dict[str, Dict[str, Any]] = {
    "batch": {"runtime": "batch", "kind": "code.cobol", "exts": COBOL_EXTS},
    "batch_nodata": {"runtime": "batch", "kind": "code.cobol", "exts": COBOL_EXTS},
    "batchmf": {"runtime": "batch", "kind": "code.cobol", "exts": COBOL_EXTS},
    "cics": {"runtime": "cics", "kind": "code.cobol", "exts": COBOL_EXTS},
    "cics_nodata": {"runtime": "cics", "kind": "code.cobol", "exts": COBOL_EXTS},
    "cicsmf": {"runtime": "cics", "kind": "code.cobol", "exts": COBOL_EXTS},
    "routine": {"runtime": "shared", "kind": "code.cobol", "exts": COBOL_EXTS},
    "copylib": {"runtime": "shared", "kind": "code.copybook", "exts": COPYBOOK_EXTS},
    "bms": {"runtime": "cics", "kind": "code.bms", "exts": BMS_EXTS},
    "listing": {"runtime": "unknown", "kind": "code.listing", "exts": LISTING_EXTS},
}


# -----------------------------
# Utilities
# -----------------------------


def die(msg: str, code: int = 1) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    raise SystemExit(code)


def read_lines(path: Path) -> List[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1").splitlines()
    except FileNotFoundError:
        die(f"input file not found: {path}")
    except Exception as exc:
        die(f"failed to read {path}: {exc}")


def stable_id(*parts: Any, length: int = 16) -> str:
    s = "||".join(str(p) for p in parts)
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return h[:length]


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()


def strip_seq(line: str) -> str:
    # COBOL sequence numbers often in columns 1-6
    if len(line) >= 6 and line[:6].isdigit():
        return line[6:]
    return line


def is_comment_line(line: str) -> bool:
    if not line:
        return False
    # Column 7 comment indicator
    if len(line) >= 7 and line[6] in ("*", "/"):
        return True
    if line.lstrip().startswith("*"):
        return True
    return False


def extract_program_id(lines: List[str]) -> Optional[str]:
    prog_re = re.compile(r"PROGRAM-ID\.\s*([A-Z0-9-]+)", re.IGNORECASE)
    for raw in lines:
        line = strip_seq(raw)
        if is_comment_line(line):
            continue
        m = prog_re.search(line)
        if m:
            return m.group(1).upper()
    return None


# -----------------------------
# COBOL anchors
# -----------------------------

DIV_RE = re.compile(r"\bDIVISION\.\s*$", re.IGNORECASE)
SEC_RE = re.compile(r"\bSECTION\.\s*$", re.IGNORECASE)
PARA_RE = re.compile(r"^\s{0,8}([A-Z0-9][A-Z0-9-]*)\.\s*$", re.IGNORECASE)


def find_cobol_anchors(lines: List[str]) -> List[int]:
    anchors: List[int] = []
    for idx, raw in enumerate(lines):
        line = strip_seq(raw)
        if is_comment_line(line):
            continue
        s = line.rstrip()
        if not s:
            continue
        if DIV_RE.search(s) or SEC_RE.search(s) or PARA_RE.match(s):
            anchors.append(idx)
    return anchors


# -----------------------------
# Chunking
# -----------------------------


def chunk_lines(
    lines: List[str],
    max_lines: int,
    overlap: int,
    anchors: Optional[List[int]] = None,
) -> List[Tuple[int, int]]:
    n = len(lines)
    if n == 0:
        return []

    if overlap >= max_lines:
        die("overlap must be smaller than max_lines")

    if not anchors:
        return _chunk_fixed(n, max_lines, overlap)

    anchors = sorted(set(a for a in anchors if 0 <= a < n))
    if 0 not in anchors:
        anchors.insert(0, 0)

    def anchor_before(pos: int) -> Optional[int]:
        import bisect
        i = bisect.bisect_right(anchors, pos) - 1
        return anchors[i] if i >= 0 else None

    chunks: List[Tuple[int, int]] = []
    start = 0
    last_start = -1
    min_lines = max(20, int(max_lines * 0.30))

    while start < n:
        end = min(start + max_lines, n)
        end_adj = anchor_before(end)
        if end_adj is not None and end_adj > start + min_lines:
            end = end_adj

        if end <= start:
            end = min(start + max_lines, n)

        chunks.append((start, end))

        if end >= n:
            break

        last_start = start
        start = max(end - overlap, start + 1)

        start_adj = anchor_before(start)
        if start_adj is not None and start_adj > last_start:
            start = start_adj

    return chunks


def _chunk_fixed(n_lines: int, max_lines: int, overlap: int) -> List[Tuple[int, int]]:
    chunks: List[Tuple[int, int]] = []
    start = 0
    while start < n_lines:
        end = min(start + max_lines, n_lines)
        chunks.append((start, end))
        if end >= n_lines:
            break
        start = max(end - overlap, start + 1)
    return chunks


# -----------------------------
# Scanning
# -----------------------------


def iter_source_files(root: Path, include_listing: bool) -> Iterable[Tuple[Path, Dict[str, Any]]]:
    for dir_name, cfg in DIR_CONFIG.items():
        if dir_name == "listing" and not include_listing:
            continue
        base = root / dir_name
        if not base.exists():
            continue
        exts = set(x.lower() for x in cfg["exts"])
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() in exts:
                yield path, cfg


# -----------------------------
# Document creation
# -----------------------------


def make_doc(
    *,
    rel_path: str,
    program: str,
    file_kind: str,
    runtime: str,
    chunk_index: int,
    chunk_count: int,
    start_line: int,
    end_line: int,
    text: str,
    content_hash: str,
) -> Dict[str, Any]:
    doc_id = stable_id(rel_path, start_line, end_line, content_hash)
    title = f"{program} {file_kind} chunk {chunk_index + 1}/{chunk_count} (lines {start_line}-{end_line})"
    header = f"{program} {file_kind} {runtime} {rel_path} lines {start_line}-{end_line}"

    return {
        "id": doc_id,
        "type": file_kind,
        "program": program,
        "title": title,
        "embedding_text": header + "\n" + text,
        "content": {
            "text": text,
            "start_line": start_line,
            "end_line": end_line,
            "num_lines": end_line - start_line + 1,
        },
        "meta": {
            "path": rel_path,
            "runtime": runtime,
            "file_kind": file_kind,
            "chunk_index": chunk_index,
            "chunk_count": chunk_count,
            "content_hash": content_hash,
            "source": "scanner_chunker",
        },
    }


# -----------------------------
# IO helpers
# -----------------------------


def load_docs(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        die(f"merge file not found: {path}")
    if path.suffix.lower() == ".jsonl":
        docs: List[Dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip():
                docs.append(json.loads(line))
        return docs
    data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    if isinstance(data, list):
        return data
    die("merge file must be JSON list or JSONL")
    return []


def write_output(docs: List[Dict[str, Any]], out_path: Path, fmt: str) -> None:
    fmt = fmt.lower()
    try:
        if fmt == "jsonl":
            with out_path.open("w", encoding="utf-8") as f:
                for d in docs:
                    f.write(json.dumps(d, ensure_ascii=False) + "\n")
        else:
            out_path.write_text(json.dumps(docs, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        die(f"failed to write {out_path}: {exc}")


# -----------------------------
# Main
# -----------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description="Scan COBOL sources and generate RAG code chunks.")
    ap.add_argument("--root", default=".", help="Base folder containing batch/cics/copylib/etc.")
    ap.add_argument("--output", "-o", default="rag_code_chunks.json", help="Output file (json or jsonl)")
    ap.add_argument("--format", "-f", choices=["json", "jsonl"], default="json", help="Output format")
    ap.add_argument("--max-lines", type=int, default=200, help="Max lines per chunk")
    ap.add_argument("--overlap", type=int, default=40, help="Line overlap between chunks")
    ap.add_argument("--include-listing", action="store_true", help="Include .lst files from listing/")
    ap.add_argument("--no-anchors", action="store_true", help="Disable anchor-aware chunking for COBOL/copybooks")
    ap.add_argument("--merge", help="Optional JSON/JSONL to merge into output")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.exists():
        die(f"root not found: {root}")

    if args.max_lines <= 0:
        die("max-lines must be > 0")
    if args.overlap < 0:
        die("overlap must be >= 0")

    all_docs: List[Dict[str, Any]] = []
    file_count = 0

    for path, cfg in iter_source_files(root, args.include_listing):
        lines = read_lines(path)
        if not lines:
            continue

        file_count += 1
        rel_path = str(path.relative_to(root)).replace("\\", "/")
        runtime = cfg["runtime"]
        file_kind = cfg["kind"]

        program = path.stem.upper()
        if file_kind in ("code.cobol", "code.copybook"):
            prog = extract_program_id(lines)
            if prog:
                program = prog

        anchors: Optional[List[int]] = None
        if not args.no_anchors and file_kind in ("code.cobol", "code.copybook"):
            anchors = find_cobol_anchors(lines)

        chunks = chunk_lines(lines, args.max_lines, args.overlap, anchors=anchors)
        total = len(chunks)

        for idx, (start, end) in enumerate(chunks):
            text = "\n".join(lines[start:end])
            content_hash = sha1_text(text)
            doc = make_doc(
                rel_path=rel_path,
                program=program,
                file_kind=file_kind,
                runtime=runtime,
                chunk_index=idx,
                chunk_count=total,
                start_line=start + 1,
                end_line=end,
                text=text,
                content_hash=content_hash,
            )
            all_docs.append(doc)

    if args.merge:
        merged = {d["id"]: d for d in load_docs(Path(args.merge))}
        for d in all_docs:
            merged[d["id"]] = d
        all_docs = list(merged.values())

    # simple stats
    counts: Dict[str, int] = {}
    for d in all_docs:
        counts[d["type"]] = counts.get(d["type"], 0) + 1

    write_output(all_docs, Path(args.output), args.format)

    print(f"[OK] Scanned {file_count} files.")
    print(f"[OK] Wrote {len(all_docs)} documents to {args.output} ({args.format}).")
    for k in sorted(counts.keys()):
        print(f"  - {k}: {counts[k]}")


if __name__ == "__main__":
    main()
