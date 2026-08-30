import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple


# ---------- CONFIG (WINDOWS PATH SAFE) ----------

# Importable whether this file is run as a script or loaded by path.
sys.path.insert(0, str(Path(__file__).resolve().parent))

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GRAPH_JSON = str(PROJECT_ROOT / "artifacts" / "intermediate" / "pdc.json")
COBOL_FILE = str(PROJECT_ROOT / "inputs" / "cobol" / "PDCBVC.CBL")
OUTPUT_JSON = str(PROJECT_ROOT / "artifacts" / "intermediate" / "pdc_enriched.json")


# ---------- HELPERS ----------

def die(msg: str, code: int = 1) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    raise SystemExit(code)


def read_json(path: Path, label: str):
    text = None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return json.loads(text)
    except FileNotFoundError:
        die(f"{label} file not found: {path}")
    except json.JSONDecodeError as exc:
        converted = parse_dot_controlflow(text or "")
        if converted is not None:
            print(f"[INFO] Converted DOT control-flow input to JSON in memory: {path}")
            return converted
        die(f"invalid JSON in {path} (line {exc.lineno}, col {exc.colno})")
    except Exception as exc:
        die(f"failed to read {path}: {exc}")


DOT_EDGE_RE = re.compile(r"<([^>]+)>\s*->\s*<([^>]+)>\s*;")
DOT_DIGRAPH_RE = re.compile(r"digraph\s+([A-Za-z0-9_]+)\s*\{", re.IGNORECASE)
DOT_RANKDIR_RE = re.compile(r"rankdir\s*=\s*([A-Za-z]+)\s*;", re.IGNORECASE)


def parse_dot_controlflow(text: str) -> Optional[Dict[str, Any]]:
    """Accept legacy DOT files accidentally named *_controlflow.json."""
    graph_match = DOT_DIGRAPH_RE.search(text)
    if not graph_match:
        return None

    nodes: set[str] = set()
    edges: List[Dict[str, str]] = []
    for source, target in DOT_EDGE_RE.findall(text):
        nodes.add(source)
        nodes.add(target)
        edges.append({"from": source, "to": target})

    if not edges:
        return None

    rank_match = DOT_RANKDIR_RE.search(text)
    return {
        "graph": {
            "name": graph_match.group(1),
            "rankdir": rank_match.group(1) if rank_match else None,
        },
        "nodes": sorted(nodes),
        "edges": edges,
    }

from cobol_conditions import (  # noqa: E402
    conjoin,
    disjoin,
    negate,
    parse_condition,
    render,
)


def norm_name(s: str) -> str:
    """Normalize COBOL paragraph/token name for matching."""
    return s.strip().upper().rstrip(".").rstrip(",")


def clean_cond(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)

    # remove trailing punctuation
    s = s.rstrip(".").rstrip(",")

    # remove trailing dangling AND/OR from multiline conditions
    s = re.sub(r"\b(AND|OR)\s*$", "", s, flags=re.I).strip()

    return s




def get_program_id(cobol_text: str) -> str:
    m = re.search(r"PROGRAM-ID\.\s*([A-Z0-9\-]+)\.", cobol_text, re.I)
    return m.group(1).upper() if m else "MAIN"


def slice_between(order: List[str], start: str, end: str) -> Optional[List[str]]:
    """Return paragraph name slice between start..end inclusive, by source order."""
    start = start.upper()
    end = end.upper()
    if start not in order or end not in order:
        return None
    i1 = order.index(start)
    i2 = order.index(end)
    if i1 > i2:
        return None
    return order[i1 : i2 + 1]

def normalize_condition(expr: str) -> str:
    """
    Fixes logical errors like:
      (X='I') AND (X='V')  -> (X='I') OR (X='V')
      (NOT (X='I')) AND (X='I') -> impossible → remove
      Progressive AND chains on same variable → OR dispatch ladder
    """

    if not expr:
        return expr

    expr = expr.strip()

    # Split top level AND parts
    parts = re.split(r"\)\s+AND\s+\(", expr)
    parts = [p.strip("() ") for p in parts]

    by_var = {}
    others = []

    for p in parts:
        m = re.match(r"([A-Z0-9\-]+)\s*=\s*'([^']+)'", p)
        if m:
            var, val = m.groups()
            by_var.setdefault(var, set()).add(val)
        else:
            others.append(p)

    rebuilt = []

    for var, vals in by_var.items():
        if len(vals) == 1:
            rebuilt.append(f"({var} = '{list(vals)[0]}')")
        else:
            ors = " OR ".join(f"({var} = '{v}')" for v in sorted(vals))
            rebuilt.append(f"({ors})")

    rebuilt.extend(others)

    if not rebuilt:
        return ""

    return " AND ".join(rebuilt)

def simplify_condition(expr: str) -> str:
    if not expr:
        return expr

    # remove double parentheses
    while expr.startswith("((") and expr.endswith("))"):
        expr = expr[1:-1]

    # A OR (A AND B)  -> A
    m = re.match(r"\((.+?)\)\s+OR\s+\(\1\s+AND\s+.+?\)", expr)
    if m:
        return f"({m.group(1)})"

    # (NOT A) AND A -> impossible
    m = re.match(r"\(NOT\s+\((.+?)\)\)\s+AND\s+\(\1\)", expr)
    if m:
        return ""   # unreachable path

    return expr



# ---------- PARSE COBOL PROCEDURE DIVISION INTO PARAGRAPHS ----------

def extract_procedure_division(cobol_text: str) -> str:
    """Return text starting at PROCEDURE DIVISION."""
    return extract_procedure_division_with_offset(cobol_text)[0]


def extract_procedure_division_with_offset(cobol_text: str) -> Tuple[str, int]:
    """Return the division text and the file line number its first line has.

    Callers that record evidence need the absolute line, and the division text
    alone cannot supply it: control-flow edges carried the statement that proved
    them but never said where it was, so a jump could be reported and not cited.
    """
    m = re.search(r"^\s*PROCEDURE\s+DIVISION\.\s*$", cobol_text, re.I | re.M)
    if not m:
        return cobol_text, 1
    # Lines fully consumed before the division text begins.
    consumed = cobol_text[: m.end()].count("\n")
    return cobol_text[m.end():], consumed + 1


AREA_A_START = 8
CODE_END = 72


def in_area_a(line: str) -> bool:
    """True when the code starts in Area A (columns 8-11), where labels live."""
    area = line[AREA_A_START - 1:CODE_END] if len(line) >= AREA_A_START else ""
    return bool(area) and area[:4].strip() != "" and not area.startswith(" ")


def parse_procedure_paragraphs(
    cobol_text: str,
) -> Tuple[Dict[str, List[str]], List[str], Dict[str, List[int]]]:
    """
    Parse paragraphs from PROCEDURE DIVISION.
    Also creates a synthetic paragraph named PROGRAM-ID containing lines
    before the first paragraph label.

    The third return value is the file line number of each retained line,
    index-aligned with the paragraph's own list. Comment lines and paragraph
    labels are skipped, so positions in the list do not correspond to offsets in
    the file and the numbers have to be carried rather than recomputed.
    """
    program_id = get_program_id(cobol_text)
    proc, first_line_no = extract_procedure_division_with_offset(cobol_text)

    paragraphs: Dict[str, List[str]] = {}
    para_line_nos: Dict[str, List[int]] = {}
    order: List[str] = []

    current = program_id
    paragraphs[current] = []
    para_line_nos[current] = []
    order.append(current)

    for offset, line in enumerate(proc.splitlines()):
        line_no = first_line_no + offset
        raw = line.rstrip()

        # Skip comment lines (classic COBOL comments often start with '*')
        if raw.strip().startswith("*"):
            continue

        # Paragraph label: NAME. in Area A. The position is what distinguishes a
        # label from a statement that happens to be a bare word and a period:
        # "EXIT." and "END-IF." sit in Area B and are statements, not paragraphs.
        # Without the column test they become phantom paragraphs, and every
        # statement after one is attributed to the phantom instead of the real
        # paragraph it belongs to.
        m = re.match(r"^\s*([A-Z0-9\-]+)\s*\.\s*$", raw, re.I) if in_area_a(raw) else None
        if m:
            current = m.group(1).upper()
            if current not in paragraphs:
                paragraphs[current] = []
                para_line_nos[current] = []
                order.append(current)
            continue

        paragraphs[current].append(raw)
        para_line_nos[current].append(line_no)

    return paragraphs, order, para_line_nos


# ---------- EXTRACT CONDITIONS FOR GO TO TARGETS ----------
class Guard(NamedTuple):
    """One guarded branch: the condition, and where the branch is written."""

    condition: str
    line: Optional[int]


def extract_paragraph_guards(
    par_lines: List[str], par_line_nos: Optional[List[int]] = None
) -> Dict[str, List[Guard]]:
    """Map each branch target to the guard conditions that reach it.

    A target can be reached under several different guards from the same
    paragraph -- three separate GO TO sites in PDCBVC lead to XCTL-LIV4 under
    unrelated conditions. Each is returned separately rather than merged into
    one expression, so the graph keeps one edge per site with the condition
    that actually guards it.

    Conditions are built as expression trees and rendered once. Nothing here
    edits condition text.
    """
    # Comments are skipped, so the line numbers have to be filtered alongside
    # the text or the two stop lining up and every branch reports a wrong line.
    numbers = list(par_line_nos or [])
    kept = [
        (text, numbers[i] if i < len(numbers) else None)
        for i, text in enumerate(par_lines)
        if not text.strip().startswith("*")
    ]
    lines: List[str] = [text for text, _ in kept]
    line_numbers: List[Optional[int]] = [number for _, number in kept]

    guards: Dict[str, List[Guard]] = {}
    cond_stack: List[Dict[str, Any]] = []
    top_level_guards: List[Any] = []

    def stack_condition():
        return conjoin(*[frame["cond"] for frame in cond_stack])

    def record(target: str, expr, index: Optional[int] = None) -> None:
        target = norm_name(target)
        if not target:
            return
        text = render(expr)
        if not text:
            return
        bucket = guards.setdefault(target, [])
        if any(existing.condition == text for existing in bucket):
            return
        line = (
            line_numbers[index]
            if index is not None and 0 <= index < len(line_numbers)
            else None
        )
        bucket.append(Guard(text, line))

    def branch_targets(text: str) -> List[str]:
        """GO TO and PERFORM targets named by one statement.

        PERFORM is included because a guarded PERFORM is a conditional edge in
        exactly the same sense as a guarded GO TO; excluding it left every
        conditional PERFORM in the corpus with no condition at all.
        """
        found: List[str] = []
        goto = re.search(r"\bGO\s+TO\b\s+([A-Z0-9-]+)", text, re.I)
        if goto:
            found.append(goto.group(1))
        perform = re.search(r"\bPERFORM\s+([A-Z0-9-]+)", text, re.I)
        if perform and perform.group(1).upper() not in {"UNTIL", "VARYING", "TIMES", "WITH"}:
            found.append(perform.group(1))
        return found

    def read_condition(index: int):
        """Read an IF/WHEN condition, following continuation lines.

        A condition split across lines leaves the connective at the end of the
        line. The trailing connective is what says the condition continues, so
        it has to be read before it is stripped -- removing it first and then
        testing for it is why multi-line conditions were silently truncated to
        their first conjunct.
        """
        raw = re.sub(r"^\s*(IF|WHEN)\b", "", lines[index], flags=re.I).strip()
        for terminator in (r"\bTHEN\b", r"\bGO\s+TO\b", r"\bPERFORM\b"):
            if re.search(terminator, raw, re.I):
                raw = re.split(terminator, raw, flags=re.I)[0].strip()
                break

        parts = [raw]
        j = index + 1
        while j < len(lines):
            nxt = lines[j].strip()
            # A condition continues either because this line ended on a
            # connective or because the next line begins with one. Only the
            # first form was recognised, so "IF (...)" followed by "AND ..."
            # lost every conjunct after the first.
            if not (_continues(parts[-1]) or _resumes(nxt)):
                break
            if re.match(r"^(ELSE|END-IF)\b", nxt, re.I):
                break
            if re.match(r"^[A-Z0-9-]+\.\s*$", nxt, re.I):
                break
            for terminator in (r"\bTHEN\b", r"\bGO\s+TO\b", r"\bPERFORM\b"):
                if re.search(terminator, nxt, re.I):
                    nxt = re.split(terminator, nxt, flags=re.I)[0].strip()
                    parts.append(nxt)
                    return parse_condition(" ".join(x for x in parts if x)), j
            parts.append(nxt)
            j += 1
        return parse_condition(" ".join(x for x in parts if x)), j

    def _continues(text: str) -> bool:
        return bool(re.search(r"(?<![A-Z0-9-])(?:AND|OR|NOT)\s*$", text or "", re.I))

    def _resumes(text: str) -> bool:
        return bool(re.match(r"^(?:AND|OR)(?![A-Z0-9-])", (text or "").strip(), re.I))

    def find_branch_in_block(start: int, limit: int = 25):
        """A classic IF whose branch statement sits further down the block."""
        depth = 0
        for k in range(start, min(len(lines), start + limit)):
            u = lines[k].strip().upper()
            if re.match(r"^(END-IF|ELSE)\b", u) and depth == 0:
                return None
            if re.match(r"^IF\b", u):
                depth += 1
                continue
            if re.match(r"^[A-Z0-9-]+\.\s*$", u):
                return None
            targets = branch_targets(u)
            if targets and depth == 0:
                return k, targets
            if u.rstrip().endswith("."):
                return None
        return None

    i = 0
    while i < len(lines):
        raw = lines[i]
        u = raw.strip().upper()

        if re.search(r"\bEND-IF\b", u):
            if cond_stack:
                cond_stack.pop()
            i += 1
            continue

        if re.match(r"^ELSE\b", u):
            if cond_stack:
                frame = cond_stack.pop()
                frame = dict(frame)
                frame["cond"] = negate(frame["cond"])
                cond_stack.append(frame)
            i += 1
            continue

        if re.match(r"^(IF|WHEN)\b", u):
            condition, j = read_condition(i)

            inline = branch_targets(u)
            if inline:
                combined = conjoin(stack_condition(), condition)
                for target in inline:
                    record(target, combined, i)
                if not cond_stack:
                    top_level_guards.append(condition)
                i = j
                continue

            following = j
            while following < len(lines) and not lines[following].strip():
                following += 1
            if following < len(lines):
                targets = branch_targets(lines[following].strip().upper())
                if targets:
                    combined = conjoin(stack_condition(), condition)
                    for target in targets:
                        record(target, combined, following)
                    if not cond_stack:
                        top_level_guards.append(condition)
                    # A period here ends the IF, so the guard must not stay on
                    # the stack: leaving it there conjoins it onto the next
                    # independent IF and reports two alternative paths as one
                    # conjunction.
                    i = following + 1
                    if not lines[following].rstrip().endswith("."):
                        cond_stack.append({"cond": condition, "implicit": True})
                    continue

            found = find_branch_in_block(j)
            if found:
                branch_index, targets = found
                combined = conjoin(stack_condition(), condition)
                for target in targets:
                    record(target, combined, branch_index)
                if not cond_stack:
                    top_level_guards.append(condition)
                i = branch_index + 1
                if not lines[branch_index].rstrip().endswith("."):
                    cond_stack.append({"cond": condition, "implicit": True})
                continue

            if not cond_stack:
                top_level_guards.clear()
            cond_stack.append({"cond": condition, "implicit": True})
            i = j
            continue

        targets = branch_targets(u)
        if targets:
            base = stack_condition()
            if base is not None:
                for target in targets:
                    record(target, base, i)
            elif top_level_guards and re.search(r"\bGO\s+TO\b", u, re.I):
                # An unguarded GO TO after a ladder of guarded ones is the
                # fallback: it is taken when none of the guards held.
                fallback = negate(disjoin(top_level_guards))
                for target in targets:
                    record(target, fallback, i)
                top_level_guards.clear()
            if raw.rstrip().endswith(".") and cond_stack and cond_stack[-1].get("implicit"):
                cond_stack.pop()
            i += 1
            continue

        if raw.rstrip().endswith("."):
            while cond_stack and cond_stack[-1].get("implicit"):
                cond_stack.pop()
        i += 1

    return guards


# ---------- DETECT PERFORM/CALL TYPES + RANGE INFO ----------

def detect_edge_type_and_meta(
    par_lines: List[str],
    target: str,
    par_line_nos: Optional[List[int]] = None,
) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Returns (etype, meta) where meta can include:
      - range_start, range_end for CALL_RANGE
      - evidence_line (the line that matched)
      - evidence_line_no (that line's number in the source file)
    """
    target = norm_name(target)

    for index, line in enumerate(par_lines):
        line_no = (
            par_line_nos[index]
            if par_line_nos is not None and index < len(par_line_nos)
            else None
        )
        u = line.upper()

        # PERFORM A THRU B
        m = re.search(r"\bPERFORM\b\s+([A-Z0-9\-]+)\s+\bTHRU\b\s+([A-Z0-9\-]+)", u, re.I)
        if m:
            start = norm_name(m.group(1))
            end = norm_name(m.group(2))
            if target == start or target == end:
                return "CALL_RANGE", {
                    "range_start": start,
                    "range_end": end,
                    "evidence_line": line.strip(),
                    "evidence_line_no": line_no,
                }

        # PERFORM A (but not THRU)
        m = re.search(r"\bPERFORM\b\s+([A-Z0-9\-]+)\b", u, re.I)
        if m and "THRU" not in u:
            callee = norm_name(m.group(1))
            if callee == target:
                return "CALL", {"evidence_line": line.strip(), "evidence_line_no": line_no}

        # GO TO A
        m = re.search(r"\bGO\s+TO\b\s+([A-Z0-9\-]+)", u, re.I)
        if m:
            goto = norm_name(m.group(1))
            if goto == target:
                return "JUMP", {"evidence_line": line.strip(), "evidence_line_no": line_no}

    return None, {}


def collect_all_perform_ranges(paragraphs: Dict[str, List[str]]) -> List[Tuple[str, str]]:
    """Collect every (start,end) from PERFORM start THRU end in the whole program."""
    ranges: List[Tuple[str, str]] = []
    for _, lines in paragraphs.items():
        for line in lines:
            u = line.upper()
            m = re.search(r"\bPERFORM\b\s+([A-Z0-9\-]+)\s+\bTHRU\b\s+([A-Z0-9\-]+)", u, re.I)
            if m:
                ranges.append((norm_name(m.group(1)), norm_name(m.group(2))))
    # remove duplicates while preserving order
    seen = set()
    out = []
    for r in ranges:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


# ---------- CICS TAGGING (PARAGRAPH-LEVEL) ----------

def detect_cics_ops(par_lines: List[str]) -> List[str]:
    """
    Extract CICS verbs ONLY from EXEC CICS ... END-EXEC blocks.
    Fixes false positives like PD1VOCI-RETURN being mistaken for EXEC CICS RETURN.
    """
    verbs = {"LINK", "SEND", "RECEIVE", "XCTL", "RETURN", "SYNCPOINT", "ADDRESS", "ASKTIME", "FORMATTIME"}
    ops: List[str] = []

    in_exec = False
    buf: List[str] = []

    def flush_block(block_text: str):
        # Find verb immediately after "EXEC CICS"
        m = re.search(r"\bEXEC\s+CICS\s+([A-Z]+)\b", block_text, re.I)
        if m:
            v = m.group(1).upper()
            if v in verbs:
                ops.append(v)

    for ln in par_lines:
        u = ln.upper()

        if not in_exec:
            if "EXEC CICS" in u:
                in_exec = True
                buf = [ln]
                if "END-EXEC" in u:
                    flush_block(" ".join(buf))
                    in_exec = False
                    buf = []
        else:
            buf.append(ln)
            if "END-EXEC" in u:
                flush_block(" ".join(buf))
                in_exec = False
                buf = []

    # unique preserve order
    seen = set()
    out = []
    for o in ops:
        if o not in seen:
            seen.add(o)
            out.append(o)
    return out



# ---------- ENRICH GRAPH ----------

def enrich_graph(graph: Dict[str, Any], cobol_text: str) -> Dict[str, Any]:
    program_id = get_program_id(cobol_text)
    paragraphs, order, para_line_nos = parse_procedure_paragraphs(cobol_text)

    # Precompute:
    # - goto conditions per paragraph
    paragraph_guards: Dict[str, Dict[str, List[Guard]]] = {
        pname: extract_paragraph_guards(lines, para_line_nos.get(pname))
        for pname, lines in paragraphs.items()
    }
    # One target can be reached under several guards from the same paragraph.
    # Track how many of each have been attached so the remainder become their
    # own edges rather than overwriting one another.
    guards_used: Dict[Tuple[str, str], int] = {}

    # - cics ops per paragraph
    cics_ops_by_par: Dict[str, List[str]] = {
        pname: detect_cics_ops(lines) for pname, lines in paragraphs.items()
    }

    # - perform ranges anywhere (for RANGE_FLOW marking)
    all_ranges = collect_all_perform_ranges(paragraphs)
    range_slices: List[Tuple[str, str, List[str]]] = []
    for start, end in all_ranges:
        sl = slice_between(order, start, end)
        if sl:
            range_slices.append((start, end, sl))

    # 1) First pass: recompute edge type, add condition + cics tagging + range meta for CALL_RANGE
    for edge in graph.get("edges", []):
        src = norm_name(edge["from"])
        tgt = norm_name(edge["to"])
        edge["from"] = src
        edge["to"] = tgt

        etype = None
        meta: Dict[str, Any] = {}

        if src in paragraphs:
            etype, meta = detect_edge_type_and_meta(
                paragraphs[src], tgt, para_line_nos.get(src)
            )

        if not etype:
            etype = "FALLTHROUGH"

        edge["type"] = etype

        # Attach the guard that reaches this target. Conditions are rendered
        # from an expression tree, so there is nothing to balance or re-wrap
        # here. A guarded PERFORM is as conditional as a guarded GO TO, so
        # edge type does not decide whether a condition applies.
        available = list(paragraph_guards.get(src, {}).get(tgt, ()))
        used = guards_used.setdefault((src, tgt), 0)
        if used < len(available):
            guard = available[used]
            edge["condition"] = guard.condition
            if guard.line is not None:
                edge["line"] = guard.line
            guards_used[(src, tgt)] = used + 1
        else:
            edge.pop("condition", None)

        # Add CALL_RANGE metadata (start/end)
        if etype == "CALL_RANGE":
            if "range_start" in meta and "range_end" in meta:
                edge["range_start"] = meta["range_start"]
                edge["range_end"] = meta["range_end"]
        else:
            edge.pop("range_start", None)
            edge.pop("range_end", None)

        # Add cics tagging on edges that "call" a paragraph that performs CICS
        if etype in ("CALL", "CALL_RANGE"):
            ops = cics_ops_by_par.get(tgt, [])
            if ops:
                edge["cics_ops"] = ops  # e.g. ["LINK"] or ["SEND"]
            else:
                edge.pop("cics_ops", None)
        else:
            edge.pop("cics_ops", None)

        # Optional: keep evidence line (useful for debugging)
        if "evidence_line" in meta:
            edge["evidence"] = meta["evidence_line"]
        if meta.get("evidence_line_no") is not None:
            # The file line the statement proving this edge sits on, so a
            # control-flow answer can cite it the way every other artifact does.
            edge["line"] = meta["evidence_line_no"]
        else:
            edge.pop("evidence", None)

    # 2) Second pass: mark internal fallthrough edges inside any PERFORM THRU range as RANGE_FLOW
    # Only upgrade edges that are sequential in source order and currently FALLTHROUGH.
    # Build a quick index for consecutive relation
    next_of = {order[i]: order[i + 1] for i in range(len(order) - 1)}

    def edge_in_slice(a: str, b: str, sl: List[str]) -> bool:
        # consecutive in order AND both in same slice
        return (a in sl) and (b in sl) and (next_of.get(a) == b)

    for edge in graph.get("edges", []):
        if edge.get("type") != "FALLTHROUGH":
            continue

        a = edge["from"]
        b = edge["to"]

        matched_ranges = []
        for start, end, sl in range_slices:
            if edge_in_slice(a, b, sl):
                matched_ranges.append({"start": start, "end": end})

        if matched_ranges:
            edge["type"] = "RANGE_FLOW"
            edge["range_flow_of"] = matched_ranges
        else:
            edge.pop("range_flow_of", None)

    # A guard with no edge to carry it is a branch the DOT export did not
    # record as a separate arc. Emitting it keeps distinct guarded paths to the
    # same target distinct, instead of silently keeping only the first.
    for source, targets in paragraph_guards.items():
        for target, conditions in targets.items():
            attached = guards_used.get((source, target), 0)
            if attached == 0 or attached >= len(conditions):
                continue
            template = next(
                (e for e in graph.get("edges", [])
                 if e.get("from") == source and e.get("to") == target),
                None,
            )
            if template is None:
                continue
            for guard in conditions[attached:]:
                edge = dict(template)
                edge["condition"] = guard.condition
                if guard.line is not None:
                    edge["line"] = guard.line
                graph.setdefault("edges", []).append(edge)

    # The graph arrives as a DOT edge list, so its node set is only the set of
    # edge endpoints. A paragraph with no edges - an EXIT-only paragraph, or one
    # nothing performs - is structurally unrepresentable and vanishes silently:
    # the graph simply reports fewer paragraphs than the program has. Union in
    # every paragraph the source declares so the node set is the program's
    # paragraph set rather than its connected subset.
    declared = {p for p in order if p}
    connected = {n for n in (graph.get("nodes") or []) if n}
    graph["nodes"] = sorted(connected | declared)

    # Add some summary metadata
    graph.setdefault("meta", {})
    graph["meta"]["isolated_nodes"] = sorted(declared - connected)
    graph["meta"]["program_id"] = program_id
    graph["meta"]["ranges_detected"] = [{"start": s, "end": e} for s, e in all_ranges]

    return graph


# ---------- RUN ----------


def main():
    import argparse

    ap = argparse.ArgumentParser(description="Enrich control-flow graph with types and conditions")
    ap.add_argument("--graph", default=GRAPH_JSON, help="Input pdc.json path")
    ap.add_argument("--cobol", default=COBOL_FILE, help="Input COBOL .CBL path")
    ap.add_argument("--out", default=OUTPUT_JSON, help="Output pdc_enriched.json path")
    ap.add_argument("--typed-out", default=None, help="Optional pdc_typed.json output path")
    args = ap.parse_args()

    graph = read_json(Path(args.graph), "graph JSON")
    try:
        cobol = Path(args.cobol).read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        die(f"COBOL file not found: {args.cobol}")
    except Exception as exc:
        die(f"failed to read COBOL file {args.cobol}: {exc}")

    enriched = enrich_graph(graph, cobol)

    try:
        Path(args.out).write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        die(f"failed to write {args.out}: {exc}")
    print(f"Enriched graph written to: {args.out}")

    if args.typed_out:
        typed_edges = []
        for e in enriched.get("edges", []):
            typed_edges.append({
                "from": e.get("from"),
                "to": e.get("to"),
                "type": e.get("type", "FALLTHROUGH"),
            })
        typed = {
            "graph": enriched.get("graph", {}),
            "nodes": enriched.get("nodes", []),
            "edges": typed_edges,
        }
        try:
            Path(args.typed_out).write_text(json.dumps(typed, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as exc:
            die(f"failed to write {args.typed_out}: {exc}")
        print(f"Typed graph written to: {args.typed_out}")


if __name__ == "__main__":
    main()
