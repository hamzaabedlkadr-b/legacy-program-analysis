import argparse
import csv
import hashlib
import io
import json
import sys
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


# -----------------------------
# Utilities
# -----------------------------

def die(msg: str, code: int = 1) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    raise SystemExit(code)


def normalize_name(x: str) -> str:
    return (x or "").strip().upper()

def stable_id(*parts: str, length: int = 16) -> str:
    """Stable short id for documents. Increase length a bit to reduce collision risk."""
    s = "||".join(parts)
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return h[:length]

def safe_int(x: Any) -> Optional[int]:
    try:
        return int(x)
    except Exception:
        return None

def parse_csv_line(line: str) -> List[str]:
    """
    MAPA result lines are comma-separated; use CSV parsing so commas in quoted fields don't break.
    """
    reader = csv.reader(io.StringIO(line), delimiter=",", quotechar='"', skipinitialspace=True)
    return next(reader, [])


# -----------------------------
# Heuristics
# -----------------------------

def classify_copybook(name: str) -> Tuple[str, float]:
    n = normalize_name(name)

    if n.startswith("DFH"):
        return ("ui_cics", 0.95)
    if n == "SQLCA" or n.startswith(("PDPSQL", "PDWSQL")) or n.endswith("SQLER") or n.startswith("SQL"):
        return ("sql", 0.85)
    if "ABEND" in n or n.startswith("PDI") or n.endswith("ABEND"):
        return ("error_handling", 0.75)
    if "UTI" in n or n.endswith("UTI01") or n.startswith("PD0UTI"):
        return ("utilities", 0.65)
    if "SAV" in n or "TWA" in n:
        return ("state_context", 0.55)
    if "SEMA" in n:
        return ("utilities", 0.6)
    if n.startswith(("PD", "PR", "PX")):
        return ("business", 0.45)
    return ("unknown", 0.2)

def classify_call_intent(call_type: str, target: str) -> Tuple[str, float]:
    ct = normalize_name(call_type)
    t = normalize_name(target)

    if "CICSXCTL" in ct:
        return ("control_transfer", 0.9)
    if "CICSLINK" in ct:
        return ("sync_service_call", 0.7)
    if "CALL" in ct:
        if "SEMA" in t:
            return ("concurrency_or_locking", 0.55)
        if "UTI" in t:
            return ("utility_service", 0.55)
        return ("subprogram_call", 0.45)
    return ("unknown", 0.2)

def interpret_db_usage(tables: List[str]) -> Tuple[str, float]:
    uniq = sorted(set(normalize_name(t) for t in tables if t))
    if not uniq:
        return ("no_db2_tables_detected", 0.9)
    if uniq == ["DUAL"]:
        return ("light_db_usage_likely_validation_or_constant_select", 0.7)
    return ("db2_tables_accessed", 0.7)


# -----------------------------
# Data model
# -----------------------------

@dataclass
class ProgramFacts:
    program: str
    file_path: Optional[str] = None
    file_timestamp: Optional[str] = None

    loc: Optional[int] = None
    statements: Optional[int] = None
    paragraphs: Optional[int] = None
    metrics_raw: List[str] = field(default_factory=list)

    copybooks: List[str] = field(default_factory=list)
    sqlincludes: List[str] = field(default_factory=list)

    # CALL record targets grouped by call_type (CALLBYIDENTIFIER, CICSLINKBYLITERAL, etc.)
    calls: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))

    # New: unresolved calls (MAPA couldn't statically resolve target)
    unresolved_calls: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))

    # New: CICS resource operations (CICSREAD, CICSWRITE, CICSSTARTBR, ...)
    # maps op -> list of resources (file/queue/dataset/map name; MAPA shows last field)
    cics_ops: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))

    # DB2 usage facts (table + stmt_type)
    db2_usage: List[Tuple[str, str]] = field(default_factory=list)

    # Traceability
    evidence: List[str] = field(default_factory=list)

    # Anything we don't handle explicitly (per program)
    unhandled_types: Counter = field(default_factory=Counter)
    unhandled_examples: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))


# -----------------------------
# Parsing MAPA result.txt
# -----------------------------

KNOWN_RECORD_TYPES = {
    "FILE", "COPY", "SQLINCLUDE", "PGM", "CALL", "UNRESOLVEDCALL", "DB2TABLE"
    # Note: CICS* are handled by prefix rule, so not listed here.
}

def parse_mapa_result(lines: List[str], example_cap: int = 3) -> Tuple[Dict[str, ProgramFacts], Counter]:
    """
    Returns: (programs, global_unhandled_counter)
    Also stores per-program unhandled examples.
    """
    programs: Dict[str, ProgramFacts] = {}
    current_prog: Optional[str] = None
    global_unhandled = Counter()

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        parts = parse_csv_line(line)
        if not parts:
            continue

        rec = (parts[0] or "").strip().upper()
        if not rec:
            continue

        if rec == "FILE":
            # FILE,<uuid>,<path>,<timestamp>
            file_path = parts[2] if len(parts) > 2 else None
            ts = parts[3] if len(parts) > 3 else None
            prog = normalize_name(Path(file_path).stem if file_path else "UNKNOWN")

            current_prog = prog
            if prog not in programs:
                programs[prog] = ProgramFacts(program=prog)
            programs[prog].file_path = file_path
            programs[prog].file_timestamp = ts
            programs[prog].evidence.append(line)
            continue

        if current_prog is None:
            current_prog = "UNKNOWN"
            if current_prog not in programs:
                programs[current_prog] = ProgramFacts(program=current_prog)

        pf = programs[current_prog]
        pf.evidence.append(line)

        # --- Explicit handlers ---
        if rec == "COPY":
            name = parts[-1] if parts else ""
            if name:
                pf.copybooks.append(normalize_name(name))

        elif rec == "SQLINCLUDE":
            name = parts[-1] if parts else ""
            if name:
                pf.sqlincludes.append(normalize_name(name))

        elif rec == "PGM":
            # PGM,<uuid>,<file-uuid>,<program>,<loc>,<statements>,<paragraphs>,...
            pf.metrics_raw = parts
            pf.loc = safe_int(parts[4]) if len(parts) > 4 else pf.loc
            pf.statements = safe_int(parts[5]) if len(parts) > 5 else pf.statements
            pf.paragraphs = safe_int(parts[6]) if len(parts) > 6 else pf.paragraphs

        elif rec == "CALL":
            # CALL,<id>,<pgm-id>,<caller>,<call-type>,<target>
            if len(parts) >= 6:
                call_type = normalize_name(parts[-2])
                target = normalize_name(parts[-1])
                if call_type and target:
                    pf.calls[call_type].append(target)

        elif rec == "UNRESOLVEDCALL":
            # UNRESOLVEDCALL,<id>,<pgm-id>,<caller>,<call-type>,<target-hint>
            if len(parts) >= 6:
                call_type = normalize_name(parts[-2])
                target = normalize_name(parts[-1])
                if call_type and target:
                    pf.unresolved_calls[call_type].append(target)

        elif rec == "DB2TABLE":
            # DB2TABLE,<id>,<pgm-id>,<table>,<stmtType>
            # Safer positional parse if schema holds:
            if len(parts) >= 5:
                table = normalize_name(parts[3])
                stmt_type = (parts[4] or "").strip()
            else:
                # fallback
                table = normalize_name(parts[-2]) if len(parts) >= 2 else ""
                stmt_type = (parts[-1] or "").strip() if len(parts) >= 1 else ""
            if table:
                pf.db2_usage.append((table, stmt_type))

        # --- Prefix handlers (CICS resource ops) ---
        elif rec.startswith("CICS"):
            # Examples from your output:
            # CICSREAD,<id>,<pgm-id>,<resource>
            # CICSSTARTBR,<id>,<pgm-id>,<resource>
            # CICSREADNEXT,...,<resource>
            # CICSWRITE,...,<resource>
            # Treat last field as "resource name" (file/queue/etc.) and store op name.
            resource = normalize_name(parts[-1]) if len(parts) >= 2 else ""
            if resource:
                pf.cics_ops[rec].append(resource)

        # --- Anything else: explicitly report as unhandled ---
        else:
            pf.unhandled_types[rec] += 1
            global_unhandled[rec] += 1
            if len(pf.unhandled_examples[rec]) < example_cap:
                pf.unhandled_examples[rec].append(line)

    # Deduplicate while preserving order
    for pf in programs.values():
        pf.copybooks = list(dict.fromkeys(pf.copybooks))
        pf.sqlincludes = list(dict.fromkeys(pf.sqlincludes))

        for ct in list(pf.calls.keys()):
            pf.calls[ct] = list(dict.fromkeys(pf.calls[ct]))

        for ct in list(pf.unresolved_calls.keys()):
            pf.unresolved_calls[ct] = list(dict.fromkeys(pf.unresolved_calls[ct]))

        for op in list(pf.cics_ops.keys()):
            pf.cics_ops[op] = list(dict.fromkeys(pf.cics_ops[op]))

        # Dedup db2_usage (table, stmt_type)
        seen = set()
        deduped = []
        for t, st in pf.db2_usage:
            key = (normalize_name(t), (st or "").strip())
            if key not in seen:
                seen.add(key)
                deduped.append(key)
        pf.db2_usage = deduped

    return programs, global_unhandled


# -----------------------------
# Evidence selection helpers
# -----------------------------

def select_evidence_for_summary(pf: ProgramFacts, max_lines: int = 6) -> List[str]:
    lines = []
    lines.extend([l for l in pf.evidence if l.startswith("FILE,")][:1])
    lines.extend([l for l in pf.evidence if l.startswith("PGM,")][:1])
    lines.extend([l for l in pf.evidence if l.startswith("CALL,")][:2])
    lines.extend([l for l in pf.evidence if l.startswith("UNRESOLVEDCALL,")][:1])
    lines.extend([l for l in pf.evidence if l.startswith("DB2TABLE,")][:1])
    return lines[:max_lines]

def select_evidence_for_copybooks(pf: ProgramFacts, max_lines: int = 5) -> List[str]:
    return [l for l in pf.evidence if l.startswith("COPY,")][:max_lines]

def select_evidence_for_database_summary(pf: ProgramFacts, max_lines: int = 6) -> List[str]:
    lines = []
    lines.extend([l for l in pf.evidence if l.startswith("SQLINCLUDE,")][:max_lines])
    lines.extend([l for l in pf.evidence if l.startswith("DB2TABLE,")][:max_lines])
    return lines[:max_lines]

def select_evidence_for_sqlinclude(pf: ProgramFacts, include: str, max_lines: int = 3) -> List[str]:
    inc = normalize_name(include)
    out = []
    for l in pf.evidence:
        if l.startswith("SQLINCLUDE,") and l.strip().endswith("," + inc):
            out.append(l)
        if len(out) >= max_lines:
            break
    return out

def select_evidence_for_db2_table(pf: ProgramFacts, table: str, max_lines: int = 3) -> List[str]:
    t = normalize_name(table)
    out = []
    for l in pf.evidence:
        if l.startswith("DB2TABLE,") and ("," + t + ",") in (l + ","):
            out.append(l)
        if len(out) >= max_lines:
            break
    return out

def select_evidence_for_call(pf: ProgramFacts, call_type: str, target: Optional[str] = None, max_lines: int = 3) -> List[str]:
    ct = normalize_name(call_type)
    lines = []
    for l in pf.evidence:
        if not l.startswith("CALL,"):
            continue
        if f",{ct}," in l:
            if target is None or l.strip().endswith("," + normalize_name(target)):
                lines.append(l)
        if len(lines) >= max_lines:
            break
    return lines

def select_evidence_for_unresolved_call(pf: ProgramFacts, call_type: str, target: Optional[str] = None, max_lines: int = 3) -> List[str]:
    ct = normalize_name(call_type)
    lines = []
    for l in pf.evidence:
        if not l.startswith("UNRESOLVEDCALL,"):
            continue
        if f",{ct}," in l:
            if target is None or l.strip().endswith("," + normalize_name(target)):
                lines.append(l)
        if len(lines) >= max_lines:
            break
    return lines

def select_evidence_for_cics_op(pf: ProgramFacts, op: str, resource: Optional[str] = None, max_lines: int = 3) -> List[str]:
    opu = normalize_name(op)
    lines = []
    for l in pf.evidence:
        if not l.upper().startswith(opu + ","):
            continue
        if resource is None or l.strip().endswith("," + normalize_name(resource)):
            lines.append(l)
        if len(lines) >= max_lines:
            break
    return lines


# -----------------------------
# Document creation
# -----------------------------

def make_doc(doc_type: str,
             program: str,
             title: str,
             content: Any,
             meta: Dict[str, Any],
             embedding_text: str,
             evidence_ref: Optional[str] = None,
             evidence: Optional[List[str]] = None) -> Dict[str, Any]:
    did = stable_id(program, doc_type, title)
    doc = {
        "id": did,
        "type": doc_type,
        "program": program,
        "title": title,
        "embedding_text": embedding_text.strip(),
        "content": content,
        "meta": meta,
    }
    if evidence_ref:
        doc["evidence_ref"] = evidence_ref
    if evidence:
        doc["evidence"] = evidence
    return doc


# -----------------------------
# Build RAG documents
# -----------------------------

def build_rag_docs(pf: ProgramFacts) -> List[Dict[str, Any]]:
    p = pf.program
    docs: List[Dict[str, Any]] = []

    # ONE raw evidence doc per program
    evidence_doc_id = stable_id(p, "evidence.mapa_raw", "raw")
    docs.append({
        "id": evidence_doc_id,
        "type": "evidence.mapa_raw",
        "program": p,
        "title": f"{p} raw MAPA lines",
        "embedding_text": f"Raw MAPA evidence for program {p}.",
        "content": {
            "lines": pf.evidence,
            "note": "Full raw MAPA lines for traceability. Other docs reference this via evidence_ref."
        },
        "meta": {"source": "mapa_result"}
    })

    # Program summary
    summary_text = f"{p} is a COBOL CICS program discovered from MAPA."
    if pf.loc is not None and pf.paragraphs is not None:
        summary_text += f" It contains approximately {pf.loc} LOC and {pf.paragraphs} paragraphs."
    if pf.file_path:
        summary_text += f" Source file: {pf.file_path}."
    if pf.unresolved_calls:
        summary_text += " It contains unresolved (dynamic) call targets."
    if pf.cics_ops:
        summary_text += " It performs CICS resource operations (READ/WRITE/etc.)."
    if pf.unhandled_types:
        summary_text += " MAPA emitted additional record types that this parser does not yet model (see unhandled docs)."

    summary_embedding = (
        f"Program {p}. COBOL CICS. "
        f"LOC={pf.loc}, paragraphs={pf.paragraphs}, statements={pf.statements}. "
        f"Source={pf.file_path or 'unknown'}. "
        f"Calls={sum(len(v) for v in pf.calls.values())}. "
        f"UnresolvedCalls={sum(len(v) for v in pf.unresolved_calls.values())}. "
        f"CICSops={sum(len(v) for v in pf.cics_ops.values())}."
    )

    docs.append(make_doc(
        "program.summary",
        p,
        f"{p} overview",
        summary_text,
        {
            "source": "mapa_result",
            "file_timestamp": pf.file_timestamp,
            "loc": pf.loc,
            "paragraphs": pf.paragraphs,
            "statements": pf.statements,
        },
        summary_embedding,
        evidence_ref=evidence_doc_id,
        evidence=select_evidence_for_summary(pf)
    ))

    # Copybooks (classified)
    classified = defaultdict(list)
    for cb in pf.copybooks:
        cat, _conf = classify_copybook(cb)
        classified[cat].append(cb)

    copybook_content = {
        "all": sorted(set(pf.copybooks)),
        "classified": {k: sorted(set(v)) for k, v in classified.items()},
        "classification_note": "Categories are heuristic; treat as hints, not ground truth."
    }

    copybook_embedding = (
        f"{p} copybooks. "
        f"UI/CICS={', '.join(sorted(set(classified.get('ui_cics', [])))) or 'none'}. "
        f"Business={', '.join(sorted(set(classified.get('business', [])))) or 'none'}. "
        f"Utilities={', '.join(sorted(set(classified.get('utilities', [])))) or 'none'}. "
        f"State={', '.join(sorted(set(classified.get('state_context', [])))) or 'none'}. "
        f"Errors={', '.join(sorted(set(classified.get('error_handling', [])))) or 'none'}."
    )

    docs.append(make_doc(
        "architecture.copybooks",
        p,
        f"{p} copybooks",
        copybook_content,
        {"source": "mapa_result", "counts": {k: len(v) for k, v in classified.items()}},
        copybook_embedding,
        evidence_ref=evidence_doc_id,
        evidence=select_evidence_for_copybooks(pf)
    ))

    # ---- DATABASE ----
    db2_tables = sorted(set(t for (t, _st) in pf.db2_usage))
    db_interpretation, db_conf = interpret_db_usage(db2_tables)

    db_summary_content = {
        "sql_includes": sorted(set(pf.sqlincludes)),
        "db2_tables": db2_tables,
        "db2_usage": [{"table": t, "stmt_type": st} for (t, st) in pf.db2_usage],
        "interpretation": db_interpretation,
        "interpretation_confidence": db_conf
    }

    db_summary_embedding = (
        f"{p} database footprint. "
        f"SQL includes: {', '.join(sorted(set(pf.sqlincludes))) or 'none'}. "
        f"DB2 tables: {', '.join(db2_tables) or 'none'}. "
        f"Interpretation: {db_interpretation} (conf={db_conf})."
    )

    docs.append(make_doc(
        "architecture.database",
        p,
        f"{p} database footprint",
        db_summary_content,
        {"source": "mapa_result"},
        db_summary_embedding,
        evidence_ref=evidence_doc_id,
        evidence=select_evidence_for_database_summary(pf)
    ))

    for inc in sorted(set(pf.sqlincludes)):
        docs.append(make_doc(
            "architecture.sqlinclude",
            p,
            f"{p} SQLINCLUDE {inc}",
            {"include": inc},
            {"source": "mapa_result", "include": inc},
            embedding_text=f"{p} includes SQL include {inc} (embedded SQL support).",
            evidence_ref=evidence_doc_id,
            evidence=select_evidence_for_sqlinclude(pf, inc)
        ))

    for (table, stmt_type) in pf.db2_usage:
        title = f"{p} DB2TABLE {table} {stmt_type}".strip()
        docs.append(make_doc(
            "architecture.db2_table",
            p,
            title,
            {"table": table, "stmt_type": stmt_type},
            {"source": "mapa_result", "table": table, "stmt_type": stmt_type},
            embedding_text=f"{p} accesses DB2 table {table} via {stmt_type or 'unknown_statement_type'}.",
            evidence_ref=evidence_doc_id,
            evidence=select_evidence_for_db2_table(pf, table)
        ))

    # ---- CALLS ----
    call_summary = {}
    for call_type, targets in pf.calls.items():
        uniq_targets = sorted(set(targets))
        intent, intent_conf = classify_call_intent(call_type, uniq_targets[0] if uniq_targets else "")
        call_summary[call_type] = {
            "targets": uniq_targets,
            "heuristic_intent": intent,
            "intent_confidence": intent_conf
        }

    docs.append(make_doc(
        "architecture.calls",
        p,
        f"{p} call summary",
        call_summary,
        {"source": "mapa_result"},
        embedding_text=(
            f"{p} calls summary. " +
            " ".join(f"{ct}: {', '.join(v['targets'])}" for ct, v in call_summary.items())
            if call_summary else f"{p} calls summary: no calls detected."
        ),
        evidence_ref=evidence_doc_id,
        evidence=[l for l in pf.evidence if l.startswith("CALL,")][:5]
    ))

    for call_type, targets in pf.calls.items():
        for t in sorted(set(targets)):
            intent_t, conf_t = classify_call_intent(call_type, t)
            docs.append(make_doc(
                "architecture.call",
                p,
                f"{p} {call_type} -> {t}",
                {
                    "caller": p,
                    "call_type": call_type,
                    "target": t,
                    "heuristic_intent": intent_t,
                    "intent_confidence": conf_t,
                    "note": "Intent labels are heuristic; verify against COBOL/CFG for accuracy."
                },
                {"source": "mapa_result", "call_type": call_type, "target": t},
                embedding_text=f"{p} calls {t} using {call_type}. Intent: {intent_t} (conf={conf_t}).",
                evidence_ref=evidence_doc_id,
                evidence=select_evidence_for_call(pf, call_type, t)
            ))

    # ---- UNRESOLVED CALLS (missing in your old script) ----
    unresolved_summary = {ct: sorted(set(tgts)) for ct, tgts in pf.unresolved_calls.items()}
    if unresolved_summary:
        docs.append(make_doc(
            "architecture.unresolved_calls",
            p,
            f"{p} unresolved call summary",
            unresolved_summary,
            {"source": "mapa_result"},
            embedding_text=(
                f"{p} has unresolved (dynamic) calls. " +
                " ".join(f"{ct}: {', '.join(tgts)}" for ct, tgts in unresolved_summary.items())
            ),
            evidence_ref=evidence_doc_id,
            evidence=[l for l in pf.evidence if l.startswith("UNRESOLVEDCALL,")][:5]
        ))

        for call_type, targets in pf.unresolved_calls.items():
            for t in sorted(set(targets)):
                docs.append(make_doc(
                    "architecture.unresolved_call",
                    p,
                    f"{p} {call_type} ~> {t}",
                    {
                        "caller": p,
                        "call_type": call_type,
                        "target_hint": t,
                        "note": "MAPA could not resolve this target statically (likely dynamic CALL/LINK)."
                    },
                    {"source": "mapa_result", "call_type": call_type, "target_hint": t},
                    embedding_text=f"{p} has unresolved call via {call_type} with target hint {t}.",
                    evidence_ref=evidence_doc_id,
                    evidence=select_evidence_for_unresolved_call(pf, call_type, t)
                ))

    # ---- CICS RESOURCE OPS (missing in your old script) ----
    cics_summary = {op: sorted(set(resources)) for op, resources in pf.cics_ops.items()}
    if cics_summary:
        docs.append(make_doc(
            "architecture.cics_resources",
            p,
            f"{p} CICS resource operations",
            cics_summary,
            {"source": "mapa_result"},
            embedding_text=(
                f"{p} performs CICS resource operations. " +
                " ".join(f"{op}: {', '.join(res)}" for op, res in cics_summary.items())
            ),
            evidence_ref=evidence_doc_id,
            evidence=[l for l in pf.evidence if l.upper().startswith("CICS")][:6]
        ))

        for op, resources in pf.cics_ops.items():
            for r in sorted(set(resources)):
                docs.append(make_doc(
                    "architecture.cics_resource_op",
                    p,
                    f"{p} {op} {r}",
                    {"operation": op, "resource": r},
                    {"source": "mapa_result", "operation": op, "resource": r},
                    embedding_text=f"{p} does {op} on resource {r}.",
                    evidence_ref=evidence_doc_id,
                    evidence=select_evidence_for_cics_op(pf, op, r)
                ))

    # ---- UNHANDLED RECORD TYPES (explicitly say what's not covered) ----
    if pf.unhandled_types:
        docs.append(make_doc(
            "analysis.unhandled_records",
            p,
            f"{p} unhandled MAPA record types",
            {
                "counts": dict(pf.unhandled_types),
                "examples": {k: v for k, v in pf.unhandled_examples.items()}
            },
            {"source": "mapa_result"},
            embedding_text=(
                f"{p} has unhandled MAPA record types: " +
                ", ".join(f"{k}({v})" for k, v in pf.unhandled_types.most_common())
            ),
            evidence_ref=evidence_doc_id,
            evidence=[],
        ))

    return docs


# -----------------------------
# IO helpers
# -----------------------------

def read_lines(path: Path) -> List[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        die(f"input file not found: {path}")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1").splitlines()
    except Exception as exc:
        die(f"failed to read {path}: {exc}")

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

def main():
    ap = argparse.ArgumentParser(description="Convert MAPA result.txt to RAG-ready JSON/JSONL documents.")
    ap.add_argument("--input", "-i", default="result.txt", help="Path to MAPA result.txt")
    ap.add_argument("--output", "-o", default="rag_documents.json", help="Output file (json or jsonl)")
    ap.add_argument("--format", "-f", choices=["json", "jsonl"], default="json", help="Output format")
    ap.add_argument("--example-cap", type=int, default=3, help="Max examples to store per unhandled record type per program")
    args = ap.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    if not in_path.exists():
        die(f"input file not found: {in_path}")

    lines = read_lines(in_path)
    programs, global_unhandled = parse_mapa_result(lines, example_cap=args.example_cap)

    all_docs: List[Dict[str, Any]] = []
    for prog, pf in sorted(programs.items(), key=lambda x: x[0]):
        all_docs.extend(build_rag_docs(pf))

    # Add a GLOBAL "unhandled types" doc so you see unknown things immediately
    if global_unhandled:
        all_docs.append({
            "id": stable_id("__GLOBAL__", "analysis.mapa_unhandled", "global"),
            "type": "analysis.mapa_unhandled",
            "program": "__GLOBAL__",
            "title": "Global unhandled MAPA record types",
            "embedding_text": "Unhandled MAPA record types encountered while parsing result.txt.",
            "content": {
                "counts": dict(global_unhandled),
                "note": "These record types were seen in the input but are not yet modeled by this script."
            },
            "meta": {"source": "mapa_result"}
        })

    # Deduplicate by id (safety)
    uniq = {}
    for d in all_docs:
        uniq[d["id"]] = d
    all_docs = list(uniq.values())

    write_output(all_docs, out_path, args.format)

    progs = ", ".join(sorted(programs.keys()))
    print(f"✔ Parsed programs: {progs}")
    print(f"✔ Wrote {len(all_docs)} RAG documents to: {out_path} ({args.format})")

    # Explicitly say what's not covered (as requested)
    if global_unhandled:
        print("\n⚠ Unhandled MAPA record types detected (not modeled yet):")
        for k, v in global_unhandled.most_common():
            print(f"  - {k}: {v} lines")
        print("  (See output doc: type=analysis.mapa_unhandled and per-program analysis.unhandled_records)\n")
    else:
        print("\n✔ No unhandled MAPA record types detected.\n")


if __name__ == "__main__":
    main()
