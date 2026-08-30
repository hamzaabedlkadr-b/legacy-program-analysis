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
  python improve_var_index_v2.py --cobol PDCBVC.CBL --cfg cfg.json --copy-dir .\\cpy --out vars_improved.json
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
    "SQL", "INCLUDE", "WHENEVER", "SQLERROR", "SQLWARNING", "NOT-FOUND",
    "SELECT", "INTO", "WHERE",
    "BEGIN", "DECLARE", "ASKTIME", "FORMATTIME",
    "SEND", "RECEIVE", "ADDRESS", "MAP", "MAPSET",
    "DATAONLY", "ERASE", "SYNCPOINT",
    "RESP", "RESP2", "LENGTH",
    "SQLCA", "SQLCODE", "SQLSTATE", "SQLERRM", "REPLACING", "SUPPRESS",
    "TITLE", "SUBTITLE", "PAGE", "COLUMNS", "FILLER",
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

# Connectives that introduce a clause but take no operands of their own. In
# fixed-format COBOL a continuation line often begins with one of these, with
# the controlling IF/EVALUATE left on an earlier physical line.
CLAUSE_CONNECTIVES = {"THEN", "ELSE"}

# Verbs that can begin an imperative statement embedded in a conditional.
STATEMENT_VERBS = WRITE_VERBS | FLOW_NO_READ_VERBS | FLOW_WITH_ARGS_VERBS | {"EXEC"}

# COBOL identifiers may contain hyphens, so \b is not a safe boundary here:
# r"\bMOVE\b" matches inside WS-MOVE-FLAG. Require a non-identifier char.
EMBEDDED_STATEMENT_RE = re.compile(
    r"(?<![A-Z0-9-])(?:"
    + "|".join(re.escape(v) for v in sorted(STATEMENT_VERBS, key=len, reverse=True))
    + r")(?![A-Z0-9-]).*"
)

PARA_RE = re.compile(r"^\s*([A-Z][A-Z0-9-]{1,30})\.\s*$")
DIV_RE = re.compile(r"^\s*(IDENTIFICATION|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION\b", re.I)
SECTION_RE = re.compile(r"^\s*([A-Z0-9-]+)\s+SECTION\.\s*$", re.I)
COPY_RE = re.compile(r"^\s*COPY\s+([A-Z0-9-]+)\b", re.I)
LEVEL_DECL_RE = re.compile(r"^\s*(\d{2})\s+([A-Z][A-Z0-9-]+)\b")

TARGET_RE = re.compile(
    r"\b(PERFORM|GO\s+TO|GO-TO|GOTO|CALL|LINK|XCTL)\s+([A-Z][A-Z0-9-]+)\b",
    re.I,
)


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
    read_write_sites: List[Site]
    subscript_sites: List[Site]
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


PROGRAM_ID_RE = re.compile(r"\bPROGRAM-ID\s*\.\s*([A-Z0-9][A-Z0-9-]*)", re.IGNORECASE)


def get_program_id(stmts: List[Tuple[int, str]]) -> str:
    """The PROGRAM-ID value, which names the implicit leading paragraph."""
    for _line, statement in stmts:
        match = PROGRAM_ID_RE.search(statement)
        if match:
            return match.group(1).upper()
    return ""


def split_into_paragraphs(
    proc_stmts: List[Tuple[int, str]], top_name: str = "TOP"
) -> Dict[str, List[Tuple[int, str]]]:
    """
    paragraph_name -> list of (line, statement)
    Filters out fake paragraph names like END-IF.
    Works on PROCEDURE DIVISION statements only.

    Statements before the first paragraph label belong to an implicit paragraph.
    The control-flow graph and the source map both name it after the program, so
    `top_name` must be the program id; a private sentinel here would produce
    citations that cannot be joined to either.
    """
    paras: Dict[str, List[Tuple[int, str]]] = {}
    current = top_name
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

    # Optional: scan copybooks in folder.
    # Every file counts, whatever it is called. A COPY member is named by the
    # COPY statement, not by a file extension, and mainframe exports routinely
    # arrive without one. Globbing for *.cpy skipped every copybook in a
    # program whose members were extensionless, which left the variables they
    # declare with no origin at all rather than with a wrong one. The sibling
    # scan in parse_declaration_relations already reads the directory this way.
    if copy_dir and copy_dir.exists():
        for cpy in sorted(path for path in copy_dir.iterdir() if path.is_file()):
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


def parse_declaration_relations(
    stmts_all: List[Tuple[int, str]],
    copy_dir: Optional[Path],
    main_source_name: str = "main_source",
) -> Dict[str, Dict]:
    """Build auditable group-membership and REDEFINES relationships."""
    relations: Dict[str, Dict] = {}

    def entry(name: str) -> Dict:
        return relations.setdefault(name, {
            "parents": [],
            "children": [],
            "redefines": [],
            "redefined_by": [],
            "declarations": [],
        })

    def add_unique_value(values: List[str], value: Optional[str]) -> None:
        if value and value not in values:
            values.append(value)

    def process(statements: List[Tuple[int, str]], source_file: str, require_data: bool) -> None:
        stack: List[Tuple[int, str]] = []
        in_data = not require_data
        for line, statement in statements:
            upper = statement.upper()
            division = DIV_RE.match(upper)
            if division:
                in_data = division.group(1).upper() == "DATA"
                stack = []
                continue
            if not in_data:
                continue
            match = LEVEL_DECL_RE.match(upper)
            if not match:
                continue
            level = int(match.group(1))
            name = match.group(2).upper()
            if is_filtered_keyword(name):
                continue
            while stack and stack[-1][0] >= level:
                stack.pop()
            parent = stack[-1][1] if stack and level not in {66, 77} else None
            item = entry(name)
            add_unique_value(item["parents"], parent)
            if parent:
                add_unique_value(entry(parent)["children"], name)
            redefines = re.search(r"\bREDEFINES\s+([A-Z][A-Z0-9-]*)\b", upper)
            if redefines:
                target = redefines.group(1).upper()
                add_unique_value(item["redefines"], target)
                add_unique_value(entry(target)["redefined_by"], name)
            declaration = {
                "line_start": line,
                "statement": statement,
                "source_file": source_file,
                "level": level,
            }
            if declaration not in item["declarations"]:
                item["declarations"].append(declaration)
            if level not in {66, 77, 88}:
                stack.append((level, name))

    process(stmts_all, main_source_name, True)
    if copy_dir and copy_dir.exists():
        for copybook in sorted(path for path in copy_dir.iterdir() if path.is_file()):
            try:
                process(read_cobol_statements(copybook), copybook.name, False)
            except Exception:
                continue
    return relations


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

def _identifiers_inside_parentheses(text: str) -> Set[str]:
    identifiers: Set[str] = set()
    for content in re.findall(r"\(([^()]*)\)", text.upper()):
        identifiers.update(extract_identifiers(content))
    return identifiers


def _receiving_identifiers(text: str) -> Tuple[Set[str], Set[str]]:
    """Return receiving fields and subscript fields from a COBOL target clause."""
    subscripts = _identifiers_inside_parentheses(text)
    depth = 0
    outside: List[str] = []
    for char in text:
        if char == "(":
            depth += 1
            outside.append(" ")
        elif char == ")":
            depth = max(0, depth - 1)
            outside.append(" ")
        else:
            outside.append(char if depth == 0 else " ")
    tokens = re.findall(r"[A-Z][A-Z0-9-]*", "".join(outside).upper())
    receivers: Set[str] = set()
    previous = ""
    for token in tokens:
        if previous not in {"OF", "IN"} and not is_filtered_keyword(token):
            receivers.add(token)
        previous = token
    return receivers, subscripts


def _target_clause(text: str) -> str:
    return re.split(
        r"\b(?:ON\s+SIZE\s+ERROR|NOT\s+ON\s+SIZE\s+ERROR|END-(?:ADD|SUBTRACT|MULTIPLY|DIVIDE|COMPUTE))\b",
        text,
        maxsplit=1,
    )[0]


def detect_statement_accesses(
    stmt: str,
) -> Tuple[Set[str], Set[str], Set[str], Set[str]]:
    """Return writes, reads, read-writes and subscript reads for one statement."""
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
        return set(), set(), set(), set()

    writes: Set[str] = set()
    reads: Set[str] = set()
    read_writes: Set[str] = set()
    subscripts: Set[str] = set()

    # Drop a leading bare connective so the statement is classified by its real
    # verb. Without this, "THEN MOVE 'LE10' TO WABEND-CODE" reaches the default
    # branch and files the receiving field as a read instead of a write.
    while words and words[0] in CLAUSE_CONNECTIVES:
        words = words[1:]
    if not words:
        return writes, reads, read_writes, subscripts
    su = " ".join(words)

    verb = words[0]

    # Fixed-format COBOL commonly places a short action on the same physical
    # statement as its condition, with or without an explicit THEN. Parse the
    # condition as reads and the embedded action with its own operand roles
    # instead of classifying the whole line as reads.
    if verb in {"IF", "WHEN"}:
        action_match = EMBEDDED_STATEMENT_RE.search(su)
        if action_match:
            reads |= set(extract_identifiers(su[: action_match.start()]))
            nested_writes, nested_reads, nested_read_writes, nested_subscripts = (
                detect_statement_accesses(action_match.group(0))
            )
            writes |= nested_writes
            reads |= nested_reads
            read_writes |= nested_read_writes
            subscripts |= nested_subscripts
        else:
            # Same conservative extraction as the default branch below.
            reads |= set(extract_identifiers(su))
        return writes, reads, read_writes, subscripts

    # Flow-only statements: do not treat targets as variable reads
    if verb in FLOW_NO_READ_VERBS:
        # However, PERFORM ... VARYING ... can include data identifiers.
        if verb == "PERFORM" and " VARYING " in su:
            reads |= set(extract_identifiers(su))
        return writes, reads, read_writes, subscripts

    # MOVE a TO b
    if verb == "MOVE":
        if " TO " in su:
            left, right = su.split(" TO ", 1)
            reads |= set(extract_identifiers(left.replace("MOVE", "", 1)))
            receivers, target_subscripts = _receiving_identifiers(_target_clause(right))
            writes |= receivers
            subscripts |= target_subscripts
            reads |= target_subscripts
        return writes, reads, read_writes, subscripts

    # COMPUTE X = expr
    if verb == "COMPUTE":
        body = su.replace("COMPUTE", "", 1)
        if "=" in body:
            left, rhs = body.split("=", 1)
            receivers, target_subscripts = _receiving_identifiers(left)
            writes |= receivers
            subscripts |= target_subscripts
            reads |= target_subscripts | set(extract_identifiers(rhs))
        return writes, reads, read_writes, subscripts

    # ADD/SUBTRACT/MULTIPLY/DIVIDE
    if verb in {"ADD", "SUBTRACT", "MULTIPLY", "DIVIDE"}:
        body = su.replace(verb, "", 1)
        if " GIVING " in body:
            source, giving = body.split(" GIVING ", 1)
            reads |= set(extract_identifiers(source))
            giving, *remainder_parts = re.split(r"\bREMAINDER\b", giving, maxsplit=1)
            receivers, target_subscripts = _receiving_identifiers(_target_clause(giving))
            writes |= receivers
            subscripts |= target_subscripts
            if remainder_parts:
                remainder_receivers, remainder_subscripts = _receiving_identifiers(
                    _target_clause(remainder_parts[0])
                )
                writes |= remainder_receivers
                subscripts |= remainder_subscripts
            reads |= subscripts
        else:
            separator = " TO " if verb == "ADD" else " FROM " if verb == "SUBTRACT" else " BY " if verb == "MULTIPLY" else " INTO "
            if separator in body:
                source, target = body.split(separator, 1)
                reads |= set(extract_identifiers(source))
                receivers, target_subscripts = _receiving_identifiers(_target_clause(target))
                writes |= receivers
                reads |= receivers | target_subscripts
                read_writes |= receivers
                subscripts |= target_subscripts
            else:
                reads |= set(extract_identifiers(body))
        return writes, reads, read_writes, subscripts

    # SET
    if verb == "SET":
        if " TO " in su:
            left, right = su.split(" TO ", 1)
            receivers, target_subscripts = _receiving_identifiers(left.replace("SET", "", 1))
            writes |= receivers
            subscripts |= target_subscripts
            reads |= set(extract_identifiers(right))
        elif " UP BY " in su:
            left, right = su.split(" UP BY ", 1)
            receivers, target_subscripts = _receiving_identifiers(left.replace("SET", "", 1))
            writes |= receivers
            reads |= receivers | target_subscripts
            read_writes |= receivers
            subscripts |= target_subscripts
            reads |= set(extract_identifiers(right))
        return writes, reads, read_writes, subscripts

    # INITIALIZE
    if verb == "INITIALIZE":
        receivers, target_subscripts = _receiving_identifiers(su.replace("INITIALIZE", "", 1))
        writes |= receivers
        reads |= target_subscripts
        subscripts |= target_subscripts
        return writes, reads, read_writes, subscripts

    # EXEC SQL / CICS
    if verb == "EXEC":
        ids = extract_identifiers(su)
        targets = extract_explicit_targets(su)

        # Host variables in SELECT ... INTO are produced by DB2. Treating them
        # as reads reverses lineage and makes correct evidence look absent.
        if re.search(r"\bEXEC\s+SQL\b", su):
            into_match = re.search(r"\bSELECT\b.*?\bINTO\b(.*?)(?:\bFROM\b|\bWHERE\b|\bEND-EXEC\b)", su)
            if into_match:
                receivers, target_subscripts = _receiving_identifiers(into_match.group(1))
                writes |= receivers
                subscripts |= target_subscripts
                reads |= target_subscripts
            reads |= set(ids) - writes - targets
            return writes, reads, read_writes, subscripts

        # RECEIVE ... INTO var => write
        if " RECEIVE " in su and " INTO " in su:
            after_into = su.split(" INTO ", 1)[1]
            writes |= set(extract_identifiers(after_into))

        # SEND ... FROM var => read
        if " SEND " in su and " FROM " in su:
            after_from = su.split(" FROM ", 1)[1]
            reads |= set(extract_identifiers(after_from))

        reads |= set(ids) - writes - targets
        return writes, reads, read_writes, subscripts

    # CALL/LINK/XCTL: ignore the target name; keep USING args as reads
    if verb in FLOW_WITH_ARGS_VERBS:
        # If USING exists, take ids after USING as reads
        if " USING " in su:
            after = su.split(" USING ", 1)[1]
            reads |= set(extract_identifiers(after))
        return writes, reads, read_writes, subscripts

    # default: conservative read extraction (procedure-only)
    reads |= set(extract_identifiers(su))
    return writes, reads, read_writes, subscripts


def detect_write_read_from_statement(stmt: str) -> Tuple[Set[str], Set[str]]:
    """Backward-compatible two-set view used by older callers."""
    writes, reads, _read_writes, _subscripts = detect_statement_accesses(stmt)
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
    declaration_relations = parse_declaration_relations(
        stmts_all,
        copy_dir=copy_dir,
        main_source_name=cobol_path.name,
    )

    stmts_proc = filter_procedure_division(stmts_all)
    program_id = get_program_id(stmts_all) or cobol_path.stem.upper()
    paragraphs = split_into_paragraphs(stmts_proc, top_name=program_id)

    cfg_adj = load_cfg(cfg_path)

    # Known paragraph names set (to prevent treating paragraph labels as vars)
    paragraph_names: Set[str] = set(paragraphs.keys())
    paragraph_names.discard(program_id)

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
            explicit_targets = extract_explicit_targets(s)
            for ident in extract_identifiers(s):
                # don't seed paragraph names as variables
                if ident in paragraph_names or ident in explicit_targets:
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

        # Fall back on naming only for the IBM-defined CICS prefixes, which are
        # part of the CICS interface rather than of any one program. A prefix
        # belonging to a particular application named its copybook's variables
        # COMMAREA here, which hid the fact that the copybook itself had failed
        # to resolve; both programs now attribute those fields to COPY:PDRTWA2.
        if origin == "UNKNOWN":
            if v.startswith(CICS_CONST_PREFIX):
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
            read_write_sites=[],
            subscript_sites=[],
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
            writes, reads, read_writes, subscripts = detect_statement_accesses(stmt)

            # record writes
            for w in writes:
                if w in info:
                    add_site(info[w].write_sites, Site(pname, ln, stmt))
                    add_unique(info[w].modified_in, pname)
                    if not info[w].defined_in:
                        add_unique(info[w].defined_in, pname)

            # record reads
            for r in reads:
                if r in info:
                    add_site(info[r].read_sites, Site(pname, ln, stmt))
                    add_unique(info[r].used_in, pname)

            for rw in read_writes:
                if rw in info:
                    add_site(info[rw].read_write_sites, Site(pname, ln, stmt))

            for subscript in subscripts:
                if subscript in info:
                    add_site(info[subscript].subscript_sites, Site(pname, ln, stmt))

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
                        if e.tgt and e.tgt not in COBOL_KEYWORDS and e.tgt != program_id:
                            add_unique(info[cv].fanout_nodes, e.tgt)

    # ---- post clean
    for v, vi in info.items():
        vi.defined_in = sorted(set(vi.defined_in))
        vi.modified_in = sorted(set(vi.modified_in))
        vi.used_in = sorted(set(vi.used_in))
        vi.fanout_nodes = sorted({x for x in vi.fanout_nodes if x and x not in COBOL_KEYWORDS and x != program_id})

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
            "relationships": declaration_relations.get(vi.variable, {
                "parents": [],
                "children": [],
                "redefines": [],
                "redefined_by": [],
                "declarations": [],
            }),
            "evidence": {
                "write_sites": [asdict(s) for s in vi.write_sites],
                "read_sites": [asdict(s) for s in vi.read_sites],
                "read_write_sites": [asdict(s) for s in vi.read_write_sites],
                "subscript_sites": [asdict(s) for s in vi.subscript_sites],
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
