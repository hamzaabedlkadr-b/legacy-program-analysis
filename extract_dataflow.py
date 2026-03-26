#!/usr/bin/env python3
"""
improve_var_index_v2.py

Improvements over your current script:
1) PROCEDURE DIVISION ONLY for read/write/control evidence (no more SPECIAL-NAMES / PIC noise)
2) Paragraph/label targets (GO TO / PERFORM / etc.) are NOT treated as variables
3) controls_flow + fanout_nodes computed primarily from CFG edge conditions (if present)
4) Better filtering of discovered identifiers (skip PIC/LEVEL keywords, numeric literals, etc.)
5) Evidence sites are still emitted (auditable)

Usage (Windows PowerShell):
  python improve_var_index_v2.py --cobol PDCBVC.CBL --cfg cfg.json --out vars_improved.json
  python improve_var_index_v2.py --cobol PDCBVC.CBL --out vars_improved.json
  python improve_var_index_v2.py --cobol PDCBVC.CBL --cfg cfg.json --copy-dir .\cpy --out vars_improved.json
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


# -----------------------------
# Config / keywords
# -----------------------------

COBOL_KEYWORDS = {
    "END-IF", "END-READ", "END-EVALUATE", "END-PERFORM", "END-EXEC",
    "IF", "ELSE", "EVALUATE", "WHEN", "PERFORM", "GO", "GOTO", "GO-TO",
    "MOVE", "COMPUTE", "ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "SET",
    "INITIALIZE", "EXEC", "CICS", "CALL", "LINK", "XCTL", "RETURN", "EXIT",
    "STOP", "RUN", "THEN", "UNTIL", "VARYING", "SEARCH", "NEXT", "SENTENCE",
    "COPY", "REPLACE", "OF", "IN", "BY", "TO", "FROM", "GIVING", "WITH",
    "AND", "OR", "NOT", "EQUAL", "EQUALS", "GREATER", "LESS",
    "PROCEDURE", "DIVISION", "DATA", "ENVIRONMENT", "IDENTIFICATION",
    "SECTION", "WORKING-STORAGE", "LINKAGE", "FILE", "LOCAL-STORAGE",
    "SPECIAL-NAMES", "INPUT-OUTPUT", "CONFIGURATION", "SKIP1", "SKIP2", "EJECT", "ZERO", "PROGRAM",
    "COMMAREA", "CONVERTING", "CURSOR", "ZEROS", "ZEROES",
    "SPACE", "SPACES",
    "HIGH-VALUE", "HIGH-VALUES",
    "LOW-VALUE", "LOW-VALUES",
    "QUOTE", "QUOTES",
    "NULL", "NULLS",
    "ALL",
    "IS", "NUMERIC", "ALPHABETIC",
    "POSITIVE", "NEGATIVE",
    "GREATER-THAN", "LESS-THAN", "EQUAL-TO","EIBAID", "EIBRESP", "EIBRESP2", "EIBTRNID",
    "DFHENTER", "DFHPF1", "DFHPF2", "DFHPF3", "DFHPF4",
    "DFHPF5", "DFHPF6", "DFHPF7", "DFHPF8", "DFHPF9",
    "DFHCLEAR", "DFHPA1", "DFHPA2", "DFHPA3",
    "SQL", "INCLUDE", "WHENEVER", "SELECT", "INTO", "WHERE",
    "BEGIN", "DECLARE", "ASKTIME", "FORMATTIME",
    "SEND", "RECEIVE", "ADDRESS", "MAP", "MAPSET",
    "DATAONLY", "ERASE", "SYNCPOINT",
    "RESP", "RESP2", "LENGTH",
    "SQLCA", "SQLCODE", "SQLSTATE", "SQLERRM", "REPLACING", "SUPPRESS",
    "TITLE", "SUBTITLE", "PAGE", "COLUMNS",
    # Data picture tokens that should never become “variables”
    "PIC", "PICTURE", "VALUE", "COMP", "COMP-3", "COMP-5", "BINARY", "DISPLAY",
    "SIGN", "SYNC", "REDEFINES", "OCCURS", "TIMES", "INDEXED", "INSPECT", "STRING", "UNSTRING",
    "ACCEPT", "DISPLAY",
    "OPEN", "CLOSE", "READ", "WRITE", "REWRITE", "DELETE",
    "START",
    "CONTINUE",
    "NEXT", "PREVIOUS",
    "ALLOCATE", "FREE",
    "MERGE", "SORT",
    "USE",# --- CICS EXEC options ---
    "ABSTIME",
    "DATESEP",
    "DDMMYY", "MMDDYY", "YYMMDD",
    "DDMMYYYY", "YYYYMMDD",
    "TIME", "DATE",
    "SYSID",
    "TRANSID",
    "TASK",
    "PROGRAM",
    "CHANNEL", "CONTAINER",
    "NOSUSPEND",
    "WAIT",
    "DELETEQ", "WRITEQ", "READQ",
    "TS", "TD",
    "QUEUE",
    "ENQ", "DEQ",
    "STARTBR", "READNEXT", "READPREV", "ENDBR",
    "ASKTIME", "FORMATTIME",# --- SQL reserved words / system objects ---
    "SELECT", "INSERT", "UPDATE", "DELETE",
    "FROM", "WHERE", "GROUP", "ORDER", "BY", "HAVING",
    "JOIN", "LEFT", "RIGHT", "INNER", "OUTER",
    "UNION", "ALL",
    "IN", "EXISTS", "LIKE", "BETWEEN",
    "NULL", "IS",
    "COUNT", "SUM", "AVG", "MIN", "MAX",
    "SYSDATE", "CURRENT_DATE", "CURRENT_TIMESTAMP",
    "DUAL",
    "COMMIT", "ROLLBACK",# --- Control-flow / labels ---
    "GO", "GOTO", "GO-TO",
    "THRU", "THROUGH",
    "EXIT"
}

# -----------------------------
# Error handling
# -----------------------------

def die(msg: str, code: int = 1) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    raise SystemExit(code)


def read_json(path: Path, label: str):
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except FileNotFoundError:
        die(f"{label} file not found: {path}")
    except json.JSONDecodeError as exc:
        die(f"invalid JSON in {path} (line {exc.lineno}, col {exc.colno})")
    except Exception as exc:
        die(f"failed to read {path}: {exc}")

# Special registers/constants we want to keep as variables even if they are keywords
SPECIAL_VARS = {
    "EIBAID", "EIBRESP", "EIBRESP2", "EIBTRNID",
    "DFHENTER", "DFHPF1", "DFHPF2", "DFHPF3", "DFHPF4",
    "DFHPF5", "DFHPF6", "DFHPF7", "DFHPF8", "DFHPF9",
    "DFHCLEAR", "DFHPA1", "DFHPA2", "DFHPA3",
}

CICS_CONST_PREFIX = ("DFH",)
CICS_EIB_PREFIX = ("EIB",)  # EIBAID, EIBTRNID, etc.

# Treat COBOL keywords as filtered unless they are CICS specials/constants
def is_filtered_keyword(tok: str) -> bool:
    t = tok.upper()
    if t in SPECIAL_VARS:
        return False
    if t.startswith(CICS_CONST_PREFIX) or t.startswith(CICS_EIB_PREFIX):
        return False
    return t in COBOL_KEYWORDS

# identifier like ABC, ABC-DEF, A1B2, etc.
IDENT_RE = re.compile(r"\b[A-Z][A-Z0-9-]*\b")

# flow statements whose “targets” are NOT data reads
FLOW_NO_READ_VERBS = {"GO", "GOTO", "GO-TO", "PERFORM"}

# flow statements where we might still have args (CALL/LINK/XCTL USING ...)
FLOW_WITH_ARGS_VERBS = {"CALL", "LINK", "XCTL"}

WRITE_VERBS = {"MOVE", "COMPUTE", "ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "SET", "INITIALIZE"}

PARA_RE = re.compile(r"^\s*([A-Z][A-Z0-9-]{1,30})\.\s*$")
DIV_RE = re.compile(r"^\s*(IDENTIFICATION|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION\b", re.I)
SECTION_RE = re.compile(r"^\s*([A-Z0-9-]+)\s+SECTION\.\s*$", re.I)
COPY_RE = re.compile(r"^\s*COPY\s+([A-Z0-9-]+)\b", re.I)
LEVEL_DECL_RE = re.compile(r"^\s*(\d{2})\s+([A-Z][A-Z0-9-]+)\b")

TARGET_RE = re.compile(r"\b(PERFORM|GO-TO|GOTO|CALL|LINK|XCTL)\s+([A-Z][A-Z0-9-]+)\b", re.I)


# -----------------------------
# Data classes
# -----------------------------

@dataclass
class Site:
    paragraph: str
    line_start: int
    statement: str

@dataclass
class VarInfo:
    variable: str
    origin: str
    defined_in: List[str]
    modified_in: List[str]
    used_in: List[str]
    controls_flow: bool
    fanout_nodes: List[str]
    write_sites: List[Site]
    read_sites: List[Site]
    control_sites: List[Site]

@dataclass
class DeclInfo:
    origin: str  # WORKING-STORAGE / LINKAGE / COMMAREA / COPY:<x> / UNKNOWN

@dataclass
class CfgEdge:
    src: str
    tgt: str
    etype: str
    condition: Optional[str] = None


# -----------------------------
# COBOL reading (fixed format friendly)
# -----------------------------

def normalize_line_fixed_format(raw: str) -> Tuple[str, bool]:
    """
    Normalize a single COBOL source line (fixed format):
      cols 1-6: sequence
      col 7: indicator
      cols 8-72: code
    Returns (code, is_continuation)
    """
    line = raw.rstrip("\n")
    if not line:
        return "", False

    padded = line + (" " * max(0, 80 - len(line)))

    indicator = padded[6] if len(padded) > 6 else " "
    if indicator in ("*", "/"):
        return "", False

    code = padded[7:72].rstrip()
    is_cont = (indicator == "-")
    return code, is_cont

def remove_quoted_literals(text: str) -> str:
    """
    Remove quoted literals before identifier extraction.
    Example:
      IF X = 'A' OR X = 'B'
    becomes:
      IF X =   OR X =
    """
    # single-quoted literals
    text = re.sub(r"'[^']*'", " ", text)
    # double-quoted literals (rare but valid)
    text = re.sub(r'"[^"]*"', " ", text)
    return text


def read_cobol_statements(path: Path) -> List[Tuple[int, str]]:
    """
    Returns list of (line_number, logical_statement).
    Joins continuation lines (indicator '-') onto the previous statement.
    """
    out: List[Tuple[int, str]] = []
    buf = ""
    buf_start_line = None

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for i, raw in enumerate(f, start=1):
            code, is_cont = normalize_line_fixed_format(raw)
            if not code:
                continue

            if is_cont and buf:
                buf += " " + code.strip()
                continue

            if buf:
                out.append((buf_start_line or i, buf.strip()))
                buf = ""
                buf_start_line = None

            buf = code
            buf_start_line = i

        if buf:
            out.append((buf_start_line or 1, buf.strip()))

    return out


def filter_procedure_division(stmts: List[Tuple[int, str]]) -> List[Tuple[int, str]]:
    """
    Keep ONLY statements that appear inside PROCEDURE DIVISION.
    This prevents SPECIAL-NAMES / PIC / WORKING-STORAGE declarations from being treated as evidence.
    """
    out: List[Tuple[int, str]] = []
    in_proc = False

    for ln, s in stmts:
        su = s.upper().strip()
        dm = DIV_RE.match(su)
        if dm:
            div = dm.group(1).upper()
            in_proc = (div == "PROCEDURE")
            continue
        if in_proc:
            out.append((ln, s))

    return out


def split_into_paragraphs(proc_stmts: List[Tuple[int, str]]) -> Dict[str, List[Tuple[int, str]]]:
    """
    paragraph_name -> list of (line, statement)
    Filters out fake paragraph names like END-IF.
    Works on PROCEDURE DIVISION statements only.
    """
    paras: Dict[str, List[Tuple[int, str]]] = {}
    current = "TOP"
    paras[current] = []

    for ln, s in proc_stmts:
        m = PARA_RE.match(s.upper())
        if m:
            name = m.group(1).upper()
            if name in COBOL_KEYWORDS:
                continue
            current = name
            paras.setdefault(current, [])
            continue
        paras.setdefault(current, []).append((ln, s))

    return paras


# -----------------------------
# DATA DIVISION origins
# -----------------------------

def parse_declarations(stmts_all: List[Tuple[int, str]], copy_dir: Optional[Path]) -> Dict[str, DeclInfo]:
    """
    Very light declaration parser (from full file):
    - Detect variables declared with level numbers in DATA DIVISION sections
    - Heuristic: 01 DFHCOMMAREA in LINKAGE => COMMAREA
    - Optional: parse copybooks in copy_dir and label as COPY:<cpy>
    """
    decls: Dict[str, DeclInfo] = {}

    in_data = False
    section = None
    commarea_mode = False

    def register(var: str, origin: str):
        var = var.upper()
        if is_filtered_keyword(var):
            return
        if var.startswith(CICS_CONST_PREFIX):
            decls[var] = DeclInfo(origin="CICS_CONST")
            return
        if var.startswith(CICS_EIB_PREFIX):
            decls[var] = DeclInfo(origin="CICS_EIB")
            return
        if var not in decls or decls[var].origin == "UNKNOWN":
            decls[var] = DeclInfo(origin=origin)

    for ln, s in stmts_all:
        su = s.upper()

        dm = DIV_RE.match(su)
        if dm:
            in_data = (dm.group(1).upper() == "DATA")
            section = None
            commarea_mode = False
            continue

        sm = SECTION_RE.match(su)
        if sm and in_data:
            section = sm.group(1).upper()
            commarea_mode = False
            continue

        lm = LEVEL_DECL_RE.match(su)
        if lm and in_data:
            level = lm.group(1)
            name = lm.group(2).upper()

            if level == "01":
                if section == "LINKAGE" and name in ("DFHCOMMAREA", "COMMAREA", "LK-COMMAREA"):
                    commarea_mode = True
                else:
                    commarea_mode = False

            if section == "WORKING-STORAGE":
                register(name, "WORKING-STORAGE")
            elif section == "LINKAGE":
                register(name, "COMMAREA" if commarea_mode else "LINKAGE")
            else:
                register(name, section or "UNKNOWN")

    # Optional: scan copybooks in folder
    if copy_dir and copy_dir.exists():
        for cpy in list(copy_dir.glob("*.cpy")) + list(copy_dir.glob("*.CPY")):
            try:
                c_stmts = read_cobol_statements(cpy)
            except Exception:
                continue
            for ln, s in c_stmts:
                su = s.upper()
                lm = LEVEL_DECL_RE.match(su)
                if lm:
                    name = lm.group(2).upper()
                    if name.startswith(CICS_CONST_PREFIX):
                        register(name, "CICS_CONST")
                    elif name.startswith(CICS_EIB_PREFIX):
                        register(name, "CICS_EIB")
                    else:
                        register(name, f"COPY:{cpy.stem.upper()}")

    return decls


# -----------------------------
# CFG helper
# -----------------------------

def load_cfg(cfg_path: Optional[Path]) -> Dict[str, List[CfgEdge]]:
    """
    Returns adjacency list: src -> list of edges.
    Supports optional edge.condition (important!).
    """
    if not cfg_path:
        return {}

    data = read_json(cfg_path, "CFG")
    edges = data.get("edges", []) or []
    adj: Dict[str, List[CfgEdge]] = {}

    for e in edges:
        src = str(e.get("from", "")).strip().upper()
        tgt = str(e.get("to", "")).strip().upper()
        et = str(e.get("type", "FALLTHROUGH")).strip().upper()
        cond = e.get("condition")
        if isinstance(cond, str):
            cond = cond.strip()
            if not cond:
                cond = None

        if not src or not tgt:
            continue

        adj.setdefault(src, []).append(CfgEdge(src=src, tgt=tgt, etype=et, condition=cond))

    return adj


# -----------------------------
# Identifier helpers
# -----------------------------

def is_literal_token(tok: str) -> bool:
    t = tok.upper()
    if t.isdigit():
        return True
    # COBOL signed literals like +1 -1
    if re.fullmatch(r"[+-]\d+", t):
        return True
    # quoted strings
    if (t.startswith("'") and t.endswith("'")) or (t.startswith('"') and t.endswith('"')):
        return True
    return False


def extract_identifiers(text: str) -> List[str]:
    """
    Extract identifiers from PROCEDURE code, excluding:
    - quoted literals ('A', 'X', 'YES', etc.)
    - keywords
    - numeric literals
    - single-letter noise
    """
    clean = remove_quoted_literals(text.upper())

    out: List[str] = []
    for m in IDENT_RE.finditer(clean):
        tok = m.group(0).upper()

        if is_filtered_keyword(tok):
            continue
        if tok.isdigit():
            continue
        if len(tok) == 1:
            # single-letter tokens are almost always literals or noise
            continue

        out.append(tok)

    return out



def extract_explicit_targets(text: str) -> Set[str]:
    """
    Extract explicit flow targets mentioned in a statement.
    """
    out: Set[str] = set()
    for m in TARGET_RE.finditer(text.upper()):
        tgt = m.group(2).upper()
        if tgt not in COBOL_KEYWORDS:
            out.add(tgt)
    return out


# -----------------------------
# Statement analysis: reads/writes
# -----------------------------

def detect_write_read_from_statement(stmt: str) -> Tuple[Set[str], Set[str]]:
    """
    Returns (writes, reads) sets for a single PROCEDURE statement (best-effort).
    Key fixes:
      - GO TO / PERFORM targets are NOT treated as reads
      - CALL/LINK/XCTL: treat USING args as reads; ignore the called target name
      - default still extracts reads (for conditions/parameters) but less noisy
    """
    su = stmt.upper().strip()
    words = su.split()
    if not words:
        return set(), set()

    verb = words[0]

    writes: Set[str] = set()
    reads: Set[str] = set()

    # Flow-only statements: do not treat targets as variable reads
    if verb in FLOW_NO_READ_VERBS:
        # However, PERFORM ... VARYING ... can include data identifiers.
        if verb == "PERFORM" and " VARYING " in su:
            reads |= set(extract_identifiers(su))
        return writes, reads

    # MOVE a TO b
    if verb == "MOVE":
        if " TO " in su:
            left, right = su.split(" TO ", 1)
            reads |= set(extract_identifiers(left.replace("MOVE", "", 1)))
            writes |= set(extract_identifiers(right))
        return writes, reads

    # COMPUTE X = expr
    if verb == "COMPUTE":
        ids = extract_identifiers(su.replace("COMPUTE", "", 1))
        if ids:
            writes.add(ids[0])
            if "=" in su:
                rhs = su.split("=", 1)[1]
                reads |= set(extract_identifiers(rhs))
            else:
                reads |= set(ids[1:])
        return writes, reads

    # ADD/SUBTRACT/MULTIPLY/DIVIDE
    if verb in {"ADD", "SUBTRACT", "MULTIPLY", "DIVIDE"}:
        if " TO " in su:
            left, right = su.split(" TO ", 1)
            reads |= set(extract_identifiers(left.replace(verb, "", 1)))
            writes |= set(extract_identifiers(right))
            reads |= set(extract_identifiers(right))
        else:
            reads |= set(extract_identifiers(su.replace(verb, "", 1)))
            if " GIVING " in su:
                giving = su.split(" GIVING ", 1)[1]
                writes |= set(extract_identifiers(giving))
        return writes, reads

    # SET
    if verb == "SET":
        if " TO " in su:
            left, right = su.split(" TO ", 1)
            writes |= set(extract_identifiers(left.replace("SET", "", 1)))
            reads |= set(extract_identifiers(right))
        elif " UP BY " in su:
            left, right = su.split(" UP BY ", 1)
            writes |= set(extract_identifiers(left.replace("SET", "", 1)))
            reads |= set(extract_identifiers(left.replace("SET", "", 1)))
            reads |= set(extract_identifiers(right))
        return writes, reads

    # INITIALIZE
    if verb == "INITIALIZE":
        writes |= set(extract_identifiers(su.replace("INITIALIZE", "", 1)))
        return writes, reads

    # EXEC CICS
    if verb == "EXEC":
        ids = extract_identifiers(su)

        # RECEIVE ... INTO var => write
        if " RECEIVE " in su and " INTO " in su:
            after_into = su.split(" INTO ", 1)[1]
            writes |= set(extract_identifiers(after_into))

        # SEND ... FROM var => read
        if " SEND " in su and " FROM " in su:
            after_from = su.split(" FROM ", 1)[1]
            reads |= set(extract_identifiers(after_from))

        reads |= set(ids) - writes
        return writes, reads

    # CALL/LINK/XCTL: ignore the target name; keep USING args as reads
    if verb in FLOW_WITH_ARGS_VERBS:
        # If USING exists, take ids after USING as reads
        if " USING " in su:
            after = su.split(" USING ", 1)[1]
            reads |= set(extract_identifiers(after))
        return writes, reads

    # default: conservative read extraction (procedure-only)
    reads |= set(extract_identifiers(su))
    return writes, reads


# -----------------------------
# Conditions
# -----------------------------

def detect_condition(stmt: str) -> Optional[str]:
    su = stmt.upper().strip()
    if su.startswith("IF "):
        return stmt.strip()
    if su.startswith("EVALUATE "):
        return stmt.strip()
    if su.startswith("WHEN "):
        return stmt.strip()
    return None


# -----------------------------
# Build improved var index
# -----------------------------

def improve_index(
    cobol_path: Path,
    cfg_path: Optional[Path],
    prev_vars_path: Optional[Path],
    copy_dir: Optional[Path],
) -> List[Dict]:
    stmts_all = read_cobol_statements(cobol_path)
    decls = parse_declarations(stmts_all, copy_dir=copy_dir)

    stmts_proc = filter_procedure_division(stmts_all)
    paragraphs = split_into_paragraphs(stmts_proc)

    cfg_adj = load_cfg(cfg_path)

    # Known paragraph names set (to prevent treating paragraph labels as vars)
    paragraph_names: Set[str] = set(paragraphs.keys())
    paragraph_names.discard("TOP")

    # ---- seed variables
    seed_vars: Set[str] = set()

    if prev_vars_path and prev_vars_path.exists():
        prev = read_json(prev_vars_path, "previous vars")
        for item in prev or []:
            v = str(item.get("variable", "")).strip().upper()
            if v:
                seed_vars.add(v)

    seed_vars |= set(decls.keys())

    # Discover from PROCEDURE only
    for pname, lines in paragraphs.items():
        for ln, s in lines:
            for ident in extract_identifiers(s):
                # don't seed paragraph names as variables
                if ident in paragraph_names:
                    continue
                seed_vars.add(ident)

    # ---- init per variable info
    info: Dict[str, VarInfo] = {}

    for v in sorted(seed_vars):
        if not v or is_filtered_keyword(v):
            continue
        if v in paragraph_names:
            continue

        origin = decls.get(v, DeclInfo(origin="UNKNOWN")).origin

        # extra heuristics (your project-specific)
        # Only apply heuristics when we couldn't detect a concrete origin.
        if origin == "UNKNOWN":
            if v.startswith("TWCOB-"):
                origin = "COMMAREA"
            elif v.startswith(CICS_CONST_PREFIX):
                origin = "CICS_CONST"
            elif v.startswith(CICS_EIB_PREFIX):
                origin = "CICS_EIB"

        info[v] = VarInfo(
            variable=v,
            origin=origin,
            defined_in=[],
            modified_in=[],
            used_in=[],
            controls_flow=False,
            fanout_nodes=[],
            write_sites=[],
            read_sites=[],
            control_sites=[],
        )

    def add_unique(lst: List[str], x: str):
        if x not in lst:
            lst.append(x)

    def add_site(lst: List[Site], s: Site):
        for existing in lst:
            if (
                existing.paragraph == s.paragraph
                and existing.line_start == s.line_start
                and existing.statement == s.statement
            ):
                return
        lst.append(s)

    # ---- pass: reads/writes/inline conditions (procedure only)
    for pname, lines in paragraphs.items():
        if pname in COBOL_KEYWORDS:
            continue

        for ln, stmt in lines:
            writes, reads = detect_write_read_from_statement(stmt)

            # record writes
            for w in writes:
                if w in info:
                    add_site(info[w].write_sites, Site(pname, ln, stmt))
                    add_unique(info[w].modified_in, pname)
                    if not info[w].defined_in:
                        add_unique(info[w].defined_in, pname)

            # record reads
            for r in reads:
                if r in info and r not in writes:
                    add_site(info[r].read_sites, Site(pname, ln, stmt))
                    add_unique(info[r].used_in, pname)

            # inline control sites (still helpful even without CFG)
            cond = detect_condition(stmt)
            if cond:
                cond_vars = set(extract_identifiers(cond))
                explicit_targets = extract_explicit_targets(cond)
                for cv in cond_vars:
                    if cv in info:
                        info[cv].controls_flow = True
                        add_site(info[cv].control_sites, Site(pname, ln, cond))
                        for t in sorted(explicit_targets):
                            if t not in COBOL_KEYWORDS:
                                add_unique(info[cv].fanout_nodes, t)

    # ---- pass: CFG condition-based fanout (preferred)
    # If your CFG edges have "condition", this is the most accurate.
    if cfg_adj:
        for src, edges in cfg_adj.items():
            for e in edges:
                if not e.condition:
                    continue
                cond_vars = set(extract_identifiers(e.condition))
                for cv in cond_vars:
                    if cv in info:
                        info[cv].controls_flow = True
                        # line numbers unknown from CFG -> use -1, keep statement as condition string
                        add_site(info[cv].control_sites, Site(src, -1, e.condition))
                        if e.tgt and e.tgt not in COBOL_KEYWORDS and e.tgt != "TOP":
                            add_unique(info[cv].fanout_nodes, e.tgt)

    # ---- post clean
    for v, vi in info.items():
        vi.defined_in = sorted(set(vi.defined_in))
        vi.modified_in = sorted(set(vi.modified_in))
        vi.used_in = sorted(set(vi.used_in))
        vi.fanout_nodes = sorted({x for x in vi.fanout_nodes if x and x not in COBOL_KEYWORDS and x != "TOP"})

        # If controls_flow true but we couldn't capture any control_sites, downgrade
        if vi.controls_flow and not vi.control_sites:
            vi.controls_flow = False

    # ---- emit
    out: List[Dict] = []
    for v in sorted(info.keys()):
        vi = info[v]
        out.append({
            "variable": vi.variable,
            "defined_in": vi.defined_in,
            "modified_in": vi.modified_in,
            "used_in": vi.used_in,
            "controls_flow": vi.controls_flow,
            "fanout_nodes": vi.fanout_nodes,
            "origin": vi.origin,
            "evidence": {
                "write_sites": [asdict(s) for s in vi.write_sites],
                "read_sites": [asdict(s) for s in vi.read_sites],
                "control_sites": [asdict(s) for s in vi.control_sites],
            }
        })

    return out


# -----------------------------
# CLI
# -----------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cobol", required=True, help="Path to COBOL .CBL/.COB file")
    ap.add_argument("--cfg", default=None, help="Path to CFG JSON (nodes/edges). Optional but improves fanout.")
    ap.add_argument("--prev", default=None, help="Path to previous variables JSON list (optional seed).")
    ap.add_argument("--copy-dir", default=None, help="Directory with copybooks (.cpy). Optional.")
    ap.add_argument("--out", required=True, help="Output JSON path")
    args = ap.parse_args()

    cobol_path = Path(args.cobol)
    cfg_path = Path(args.cfg) if args.cfg else None
    prev_path = Path(args.prev) if args.prev else None
    copy_dir = Path(args.copy_dir) if args.copy_dir else None
    out_path = Path(args.out)

    if not cobol_path.exists():
        die(f"COBOL file not found: {cobol_path}")
    if cfg_path and not cfg_path.exists():
        die(f"CFG file not found: {cfg_path}")
    if prev_path and not prev_path.exists():
        die(f"previous vars file not found: {prev_path}")
    if copy_dir and not copy_dir.exists():
        die(f"copybook directory not found: {copy_dir}")

    improved = improve_index(
        cobol_path=cobol_path,
        cfg_path=cfg_path,
        prev_vars_path=prev_path,
        copy_dir=copy_dir,
    )

    try:
        out_path.write_text(json.dumps(improved, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        die(f"failed to write {out_path}: {exc}")
    print(f"[OK] Wrote {len(improved)} variables to: {out_path}")


if __name__ == "__main__":
    main()
