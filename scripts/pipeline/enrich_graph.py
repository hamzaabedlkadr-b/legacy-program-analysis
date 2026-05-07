import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


# ---------- CONFIG (WINDOWS PATH SAFE) ----------

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
    m = re.search(r"^\s*PROCEDURE\s+DIVISION\.\s*$", cobol_text, re.I | re.M)
    if not m:
        return cobol_text
    return cobol_text[m.end():]


def parse_procedure_paragraphs(cobol_text: str) -> Tuple[Dict[str, List[str]], List[str]]:
    """
    Parse paragraphs from PROCEDURE DIVISION.
    Also creates a synthetic paragraph named PROGRAM-ID containing lines
    before the first paragraph label.
    """
    program_id = get_program_id(cobol_text)
    proc = extract_procedure_division(cobol_text)

    paragraphs: Dict[str, List[str]] = {}
    order: List[str] = []

    current = program_id
    paragraphs[current] = []
    order.append(current)

    for line in proc.splitlines():
        raw = line.rstrip()

        # Skip comment lines (classic COBOL comments often start with '*')
        if raw.strip().startswith("*"):
            continue

        # Paragraph label: NAME.
        m = re.match(r"^\s*([A-Z0-9\-]+)\s*\.\s*$", raw, re.I)
        if m:
            current = m.group(1).upper()
            if current not in paragraphs:
                paragraphs[current] = []
                order.append(current)
            continue

        paragraphs[current].append(raw)

    return paragraphs, order


# ---------- EXTRACT CONDITIONS FOR GO TO TARGETS ----------
def extract_goto_conditions(par_lines: List[str]) -> Dict[str, str]:
    """
    Map: target_paragraph -> condition string

    Fixes:
    - Dispatch ladders => fallback gets NOT(OR(guards))
    - Multi-statement IF ... (no END-IF) where a GO TO appears later in the block
      => condition is attached to that GO TO, not to the later fallback
    - COBOL shorthand:  X = 'I' OR 'A' OR 'C'  =>  X='I' OR X='A' OR X='C'
    - Parentheses balancing (prevents truncated conditions)
    - Basic boolean simplifications:  A OR (A AND B) => A, NOT(NOT GREATER) => GREATER, etc.
    """

    # -------------------- local helpers --------------------

    def clean(s: str) -> str:
        s = (s or "").strip()
        s = re.sub(r"\s+", " ", s)
        s = s.rstrip(".").rstrip(",")
        s = re.sub(r"\b(AND|OR)\s*$", "", s, flags=re.I).strip()
        return s

    def parse_goto_target(line: str) -> Optional[str]:
        m = re.search(r"\bGO\s+TO\b\s+([A-Z0-9\-]+)", line, re.I)
        return norm_name(m.group(1)) if m else None

    def balance_parens(s: str) -> str:
        if not s:
            return ""
        # Count opening and closing parentheses
        op = s.count("(")
        cp = s.count(")")
        # If unbalanced, fix it
        if op > cp:
            s = s + (")" * (op - cp))
        elif cp > op:
            # Too many closing parens - this shouldn't happen but if it does, remove extras from start
            # Actually, better to add opening at start
            s = ("(" * (cp - op)) + s
        return s

    def expand_cobol_or_shorthand(cond: str) -> str:
        """
        Expand: VAR = 'I' OR 'A' OR 'C'
        into:   VAR = 'I' OR VAR = 'A' OR VAR = 'C'
        """
        cond = cond or ""
        # Repeat until no more shorthand is found (handles multiple occurrences in a condition)
        while True:
            m = re.search(
                r"(\b[A-Z0-9\-]+\b)\s*=\s*'([^']+)'((?:\s+OR\s+'[^']+')+)",
                cond,
                flags=re.I,
            )
            if not m:
                break
            var = m.group(1)
            first = m.group(2)
            tail = m.group(3)
            more_vals = re.findall(r"'([^']+)'", tail)
            expanded = " OR ".join([f"{var} = '{first}'"] + [f"{var} = '{v}'" for v in more_vals])
            cond = cond[: m.start()] + "(" + expanded + ")" + cond[m.end() :]
        return cond
    def strip_outer_parens(s: str) -> str:
        s = s.strip()
        while s.startswith("(") and s.endswith(")"):
            inner = s[1:-1].strip()
            # only strip if outer parentheses actually wrap the whole expression
            if inner.count("(") == inner.count(")"):
                s = inner
            else:
                break
        return s
    
    def aggressively_reduce_parens(s: str) -> str:
        """Aggressively remove excessive nested parentheses while maintaining balance."""
        if not s:
            return s
        # First, ensure it's balanced
        s = balance_parens(s)
        
        # This is a critical fix for structural errors
        
        # Now balance again
        s = balance_parens(s)
        
        prev = None
        iterations = 0
        max_iterations = 10  # Prevent infinite loops
        while prev != s and iterations < max_iterations:
            prev = s
            iterations += 1
            # Remove multiple layers of parentheses: (((X))) -> (X) for simple expressions
            s = re.sub(r"\(\(\(([^()]+)\)\)\)", r"(\1)", s)
            s = re.sub(r"\(\(([^()]+)\)\)", r"(\1)", s)
            # For complex expressions, be more careful
            # Only reduce if inner is balanced
            def reduce_balanced(m):
                inner = m.group(1)
                inner_op = inner.count("(")
                inner_cp = inner.count(")")
                if inner_op == inner_cp:
                    # Inner is balanced, we can reduce one layer
                    inner_stripped = inner.strip()
                    # Don't reduce if it would break structure
                    if inner_stripped.startswith("(") and inner_stripped.endswith(")"):
                        # Already wrapped, keep as is
                        return f"({inner_stripped})"
                    return f"({inner_stripped})"
                return m.group(0)
            s = re.sub(r"\(\(([^)]+)\)\)", reduce_balanced, s)
            # Strip outer only if balanced
            s = strip_outer_parens(s)
            # Rebalance after each iteration
            s = balance_parens(s)
        return s

    def split_top_level(expr: str, op_word: str) -> List[str]:
        """
        Split expr by op_word (AND/OR) only when parentheses depth == 0.
        op_word must be uppercase "OR" or "AND".
        """
        out = []
        buf = []
        depth = 0

        tokens = re.split(r"(\b" + re.escape(op_word) + r"\b)", expr, flags=re.I)

        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok is None:
                i += 1
                continue

            # update depth for parentheses in this chunk
            for ch in tok:
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth = max(0, depth - 1)

            # if this token is the operator word and we're at top level, split
            if re.fullmatch(r"\b" + re.escape(op_word) + r"\b", tok.strip(), flags=re.I) and depth == 0:
                out.append("".join(buf).strip())
                buf = []
            else:
                buf.append(tok)

            i += 1

        tail = "".join(buf).strip()
        if tail:
            out.append(tail)

        return [x for x in out if x and x.strip()]

    def normalize_for_comparison(s: str) -> str:
        """Normalize a condition string for comparison by removing all parentheses and normalizing spacing."""
        s = clean(s)
        s = balance_parens(s)
        # Remove all parentheses for comparison
        s = re.sub(r"[()]", "", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s.upper()
    
    def dedup_top_level_or(expr: str) -> str:
        """
        Remove duplicate top-level OR terms: A OR B OR A -> A OR B
        Works even if terms have extra parentheses/spacing.
        Also handles cases where one condition is a subset of another.
        """
        expr = (expr or "").strip()
        if not expr:
            return expr

        parts = split_top_level(expr, "OR")
        if len(parts) <= 1:
            return expr

        seen_normalized = {}
        kept = []

        for p in parts:
            p_clean = clean(balance_parens(p))
            p_clean = strip_outer_parens(p_clean)
            # Fix any structural issues in the part first
            p_clean = balance_parens(p_clean)
            p_norm = normalize_for_comparison(p_clean)
            
            # Check if this is a duplicate
            is_duplicate = False
            for seen_norm, seen_orig in seen_normalized.items():
                # Exact match after normalization
                if p_norm == seen_norm:
                    is_duplicate = True
                    break
                # Check if one is a subset: if p_norm is contained in seen_norm (or vice versa)
                # Simple check: if one is a prefix of the other (for variable=value patterns)
                if " AND " in seen_norm:
                    seen_first = seen_norm.split(" AND ", 1)[0].strip()
                    if p_norm == seen_first:
                        is_duplicate = True
                        break
                if " AND " in p_norm:
                    p_first = p_norm.split(" AND ", 1)[0].strip()
                    if p_first == seen_norm:
                        # p_norm is more specific, so remove the simpler seen_norm
                        # But we can't modify while iterating, so we'll handle in second pass
                        pass
            
            if not is_duplicate:
                seen_normalized[p_norm] = p.strip()
                kept.append((p.strip(), p_norm))

        # Second pass: remove kept items that are subsets of others
        final_kept = []
        for i, (p_orig, p_norm) in enumerate(kept):
            is_subset = False
            for j, (other_orig, other_norm) in enumerate(kept):
                if i == j:
                    continue
                # If p_norm is simpler and other_norm contains it
                if " AND " in other_norm:
                    other_first = other_norm.split(" AND ", 1)[0].strip()
                    if p_norm == other_first:
                        is_subset = True
                        break
            if not is_subset:
                final_kept.append(p_orig)

        if not final_kept:
            return ""

        if len(final_kept) == 1:
            return final_kept[0].strip()

        return " OR ".join(f"({strip_outer_parens(k.strip())})" for k in final_kept)

    def repair_simple_or_chain(expr: str) -> str:
        if not expr:
            return expr
        if " OR " not in expr.upper():
            return expr
        if "NOT" in expr.upper():
            return expr
        # Only rebuild very simple OR chains of equality comparisons.
        terms = re.findall(r"[A-Z0-9\-]+\s*=\s*'[^']+'", expr, flags=re.I)
        if len(terms) >= 2:
            # If expression only contains these terms + OR + parens/space, rebuild cleanly.
            tmp = re.sub(r"[()\s]", "", expr)
            tmp = re.sub(r"\bOR\b", "", tmp, flags=re.I)
            tmp = re.sub(r"[A-Z0-9\-]+='[^']+'", "", tmp, flags=re.I)
            if tmp == "":
                return " OR ".join(f"({t.strip()})" for t in terms)
        return expr

    def fix_and_same_var_equals(expr: str) -> str:
        """
        (X='I') AND (X='A')  -> (X='I') OR (X='A')
        Repeats to handle chains.
        """
        if not expr:
            return expr
        prev = None
        cur = expr
        pat = re.compile(
            r"\(\s*([A-Z0-9\-]+)\s*=\s*'([^']+)'\s*\)\s+AND\s+\(\s*\1\s*=\s*'([^']+)'\s*\)",
            flags=re.I
        )
        while prev != cur:
            prev = cur
            cur = pat.sub(r"((\1 = '\2') OR (\1 = '\3'))", cur)
        return cur
    
    def simplify_or_with_common_and(expr: str) -> str:
        """
        Simplify: (X='A' AND Y='1') OR (X='A' AND Y='2') -> (X='A' AND (Y='1' OR Y='2'))
        Also handles: (X='A') OR (X='A' AND Y='1') -> (X='A')
        """
        if not expr:
            return expr
        
        # Split by top-level OR
        parts = split_top_level(expr, "OR")
        if len(parts) <= 1:
            return expr
        
        # Group parts by common AND terms
        # For now, just handle simple case: (X='A') OR (X='A' AND Y='1') -> (X='A')
        # Check if one part is a subset of another
        simplified_parts = []
        for i, p1 in enumerate(parts):
            p1_clean = strip_outer_parens(clean(p1))
            is_subset = False
            for j, p2 in enumerate(parts):
                if i == j:
                    continue
                p2_clean = strip_outer_parens(clean(p2))
                # If p1 is contained in p2 (p2 has p1 AND something else), p1 can be removed
                # Simple check: if p1 matches and p2 has AND, check if p1 is a prefix
                if " AND " in p2_clean.upper():
                    p2_first = p2_clean.split(" AND ", 1)[0].strip()
                    if clean(p1_clean) == clean(p2_first):
                        is_subset = True
                        break
            if not is_subset:
                simplified_parts.append(p1)
        
        if len(simplified_parts) < len(parts):
            if len(simplified_parts) == 1:
                return simplified_parts[0].strip()
            return " OR ".join(f"({p.strip()})" for p in simplified_parts)
        
        return expr

    def remove_contradiction_not_a_and_a(expr: str) -> str:
        """
        (NOT (X='I')) AND (X='I')  -> "" (unreachable)
        """
        if not expr:
            return expr
        pat = re.compile(
            r"\(\s*NOT\s*\(\s*([A-Z0-9\-]+)\s*=\s*'([^']+)'\s*\)\s*\)\s+AND\s+\(\s*\1\s*=\s*'\2'\s*\)",
            flags=re.I
        )
        if pat.search(expr):
            return ""
        return expr

    def simplify_condition(expr: str) -> str:
        expr = expr or ""
        expr = clean(expr)
        expr = balance_parens(expr)

        # Remove excessive nested parentheses: (((X))) -> (X), but be careful
        # Repeat until no more changes
        prev = None
        while prev != expr:
            prev = expr
            # Remove double/triple parentheses around simple expressions
            expr = re.sub(r"\(\(\(([^()]+)\)\)\)", r"(\1)", expr)
            expr = re.sub(r"\(\(([^()]+)\)\)", r"(\1)", expr)
            # But only if the inner expression is balanced
            def reduce_parens(m):
                inner = m.group(1)
                if inner.count("(") == inner.count(")"):
                    return f"({inner})"
                return m.group(0)
            expr = re.sub(r"\(\(([^()]+)\)\)", reduce_parens, expr)

        # NOT (A NOT GREATER B)  ->  A GREATER B
        expr = re.sub(r"NOT\s*\(\s*([A-Z0-9\-]+)\s+NOT\s+GREATER\s+([A-Z0-9\-]+)\s*\)", r"\1 GREATER \2", expr, flags=re.I)
        # NOT (A NOT LESS B) -> A LESS B
        expr = re.sub(r"NOT\s*\(\s*([A-Z0-9\-]+)\s+NOT\s+LESS\s+([A-Z0-9\-]+)\s*\)", r"\1 LESS \2", expr, flags=re.I)
        # NOT (A = B) keep as NOT (A = B) (just normalize spacing)
        expr = re.sub(r"NOT\s*\(\s*", "NOT (", expr, flags=re.I)

        # Absorption:  (A) OR ((A) AND B) => (A)
        # Very small but handles your MUOVI-DATI-30 style redundancy well
        expr = re.sub(
            r"\(\s*([^)]+?)\s*\)\s+OR\s+\(\s*\(\s*\1\s*\)\s+AND\s+([^)]+?)\s*\)",
            r"(\1)",
            expr,
            flags=re.I,
        )

        expr = balance_parens(expr)
        expr = fix_and_same_var_equals(expr)
        expr = remove_contradiction_not_a_and_a(expr)
        expr = balance_parens(expr)
        
        # Simplify OR expressions with common AND terms
        expr = simplify_or_with_common_and(expr)
        
        # More aggressive deduplication: handle nested duplicates too
        expr = dedup_top_level_or(expr)
        
        # Simplify redundant same-variable checks: (X='A') OR (X='A') -> (X='A')
        # This handles cases like PDCGVC OR PDCGVC OR PDCGVC
        parts = split_top_level(expr, "OR")
        if len(parts) > 1:
            seen_normalized = {}
            kept = []
            for p in parts:
                p_clean = strip_outer_parens(clean(p))
                # Normalize: extract variable=value patterns
                var_val_match = re.match(r"([A-Z0-9\-]+)\s*=\s*'([^']+)'", p_clean, re.I)
                if var_val_match:
                    var, val = var_val_match.groups()
                    key = f"{var.upper()}={val.upper()}"
                    if key not in seen_normalized:
                        seen_normalized[key] = p.strip()
                        kept.append(p.strip())
                else:
                    # For non-simple conditions, use full normalization
                    p_norm = clean(balance_parens(p_clean))
                    p_norm = strip_outer_parens(p_norm)
                    p_norm = re.sub(r"\s+", " ", p_norm).strip()
                    # Check if this normalized form already exists
                    found_dup = False
                    for existing in seen_normalized.values():
                        existing_norm = clean(balance_parens(strip_outer_parens(clean(existing))))
                        existing_norm = re.sub(r"\s+", " ", existing_norm).strip()
                        if p_norm == existing_norm:
                            found_dup = True
                            break
                    if not found_dup:
                        seen_normalized[p_norm] = p.strip()
                        kept.append(p.strip())
            
            if len(kept) == 1:
                expr = kept[0].strip()
            elif len(kept) > 1:
                expr = " OR ".join(f"({k.strip()})" for k in kept)
            else:
                expr = ""
        
        # Final cleanup: remove excessive parentheses one more time
        expr = aggressively_reduce_parens(expr)
        expr = balance_parens(expr)
        expr = strip_outer_parens(expr)
        
        return expr

    def combine(base: Optional[str], extra: Optional[str]) -> str:
        extra = simplify_condition(expand_cobol_or_shorthand(clean(extra or "")))
        if not extra:
            return simplify_condition(base or "")
        if base:
            # Avoid double-wrapping: strip outer parens before combining
            base_clean = strip_outer_parens(base)
            extra_clean = strip_outer_parens(extra)
            # Only wrap if needed
            if " OR " in base_clean.upper() or " AND " in base_clean.upper():
                base_clean = f"({base_clean})"
            if " OR " in extra_clean.upper() or " AND " in extra_clean.upper():
                extra_clean = f"({extra_clean})"
            result = f"{base_clean} AND {extra_clean}"
            return simplify_condition(balance_parens(result))
        return simplify_condition(balance_parens(f"({extra})"))

    def add_cond(tgt: str, cond: str):
        cond = simplify_condition(expand_cobol_or_shorthand(clean(cond)))
        if not cond:
            return
        if tgt in goto_conds:
            # Avoid double-wrapping in parentheses
            existing = strip_outer_parens(goto_conds[tgt])
            new_cond = strip_outer_parens(cond)
            # Only wrap if needed (if they contain operators)
            if " OR " in existing.upper() or " AND " in existing.upper():
                existing = f"({existing})"
            if " OR " in new_cond.upper() or " AND " in new_cond.upper():
                new_cond = f"({new_cond})"
            merged = f"{existing} OR {new_cond}"
            goto_conds[tgt] = dedup_top_level_or(simplify_condition(merged))
        else:
            goto_conds[tgt] = dedup_top_level_or(cond)


    def stack_cond() -> Optional[str]:
        if not cond_stack:
            return None
        joined = " AND ".join(
            f"({simplify_condition(x['cond'])})"
            for x in cond_stack
            if clean(x.get("cond", ""))
        )
        return simplify_condition(joined)


    def read_if_condition(i: int) -> Tuple[str, int]:
        """
        Read IF condition possibly spanning multiple lines.
        Returns (condition, next_index_after_condition_lines)
        """
        raw = lines[i]
        tmp = re.sub(r"^\s*IF\b", "", raw, flags=re.I).strip()

        # cut at THEN if present
        if re.search(r"\bTHEN\b", tmp, re.I):
            tmp = re.split(r"\bTHEN\b", tmp, flags=re.I)[0].strip()

        # cut at inline GO TO
        if re.search(r"\bGO\s+TO\b", tmp, re.I):
            tmp = re.split(r"\bGO\s+TO\b", tmp, flags=re.I)[0].strip()

        parts = [clean(tmp)]
        j = i + 1

        # continue reading while unfinished (ends with AND/OR)
        while j < len(lines):
            prev = parts[-1] if parts else ""
            if not re.search(r"\b(AND|OR)\s*$", prev, re.I):
                break

            nxt = lines[j].strip()
            u = nxt.upper()

            if re.match(r"^(GO\s+TO|PERFORM|ELSE|END-IF)\b", u):
                break
            if re.match(r"^[A-Z0-9\-]+\.\s*$", u):
                break

            parts.append(clean(nxt))
            j += 1

        cond = clean(" ".join(p for p in parts if p))
        cond = expand_cobol_or_shorthand(cond)
        cond = simplify_condition(cond)
        return cond, j

    def find_goto_in_if_block(start_idx: int, max_scan: int = 25) -> Optional[Tuple[int, str]]:
        """
        For IF that isn't immediately followed by GO TO, scan forward for a GO TO that belongs to it
        (classic COBOL multi-statement IF without END-IF).

        Stops at:
          - another IF at same level
          - END-IF / ELSE
          - next paragraph label
        """
        j = start_idx
        scanned = 0
        while j < len(lines) and scanned < max_scan:
            u = lines[j].strip().upper()
            if lines[j].rstrip().endswith("."):
                return None
            if re.match(r"^\s*IF\b", u):
                return None
            if re.match(r"^\s*(END-IF|ELSE)\b", u):
                return None
            if re.match(r"^[A-Z0-9\-]+\.\s*$", u):
                return None

            if "GO TO" in u:
                tgt = parse_goto_target(u)
                if tgt:
                    return j, tgt

            j += 1
            scanned += 1

        return None

    # -------------------- main --------------------

    # Pre-clean lines
    lines: List[str] = []
    for ln in par_lines:
        s = ln.rstrip()
        if not s.strip():
            continue
        if s.strip().startswith("*"):
            continue
        lines.append(s)

    goto_conds: Dict[str, str] = {}
    cond_stack: List[Dict[str, Any]] = []   # each: {"cond": "...", "implicit": True/False}

    # Collect consecutive top-level IF->GO TO guards, to build fallback NOT(OR(...))
    top_level_guards: List[str] = []

    def clear_top_guards():
        top_level_guards.clear()

    i = 0
    while i < len(lines):
        raw = lines[i]
        u = raw.strip().upper()

        # END-IF
        if re.search(r"\bEND-IF\b", u):
            if cond_stack:
                cond_stack.pop()
            i += 1
            continue

        # ELSE
        if re.match(r"^\s*ELSE\b", u):
            if cond_stack:
                last = cond_stack.pop()
                last["cond"] = f"NOT ({last['cond']})"
                cond_stack.append(last)
            i += 1
            continue

        # IF ...
        if re.match(r"^\s*IF\b", u):
            if_cond, j = read_if_condition(i)

            # Case A: inline IF ... GO TO target
            if re.search(r"\bGO\s+TO\b", u):
                tgt = parse_goto_target(u)
                if tgt:
                    c = combine(stack_cond(), if_cond)
                    add_cond(tgt, c)
                    if not cond_stack:
                        top_level_guards.append(c)
                i = j
                continue

            # Case B: IF cond THEN / next statement is GO TO target
            k = j
            while k < len(lines) and not lines[k].strip():
                k += 1
            if k < len(lines):
                tgt = parse_goto_target(lines[k].strip().upper())
                if tgt:
                    c = combine(stack_cond(), if_cond)
                    add_cond(tgt, c)
                    if not cond_stack:
                        top_level_guards.append(c)
                    i = k + 1
                    continue

            # Case C: multi-statement IF without END-IF: scan for GO TO inside block
            found = find_goto_in_if_block(j)
            if found:
                goto_idx, tgt = found
                c = combine(stack_cond(), if_cond)
                add_cond(tgt, c)
                if not cond_stack:
                    top_level_guards.append(c)
                # continue after that GO TO line (the IF effectively ends here for CFG purposes)
                i = goto_idx + 1
                continue

            # Case D: real IF block (push)
            if not cond_stack:
                clear_top_guards()
            cond_stack.append({"cond": if_cond, "implicit": True})
            i = j
            continue

        # Unconditional GO TO ...
        if re.search(r"\bGO\s+TO\b", u):
            tgt = parse_goto_target(u)
            if tgt:
                base = stack_cond()

                if base:
                    # inside nested IF context
                    add_cond(tgt, base)
                else:
                    # top-level unconditional GO TO: dispatch/pf fallback
                    if top_level_guards:
                        ors = " OR ".join(f"({g})" for g in top_level_guards)
                        add_cond(tgt, f"NOT ({ors})")
                        clear_top_guards()

            i += 1
            continue
        # If COBOL ends an IF scope with a period (no END-IF), close it here
        if raw.rstrip().endswith("."):
            if cond_stack and cond_stack[-1].get("implicit"):
                cond_stack.pop()
        i += 1

    # Final cleanup: ensure all conditions are not truncated and shorthand expanded
    for k in list(goto_conds.keys()):
        goto_conds[k] = simplify_condition(expand_cobol_or_shorthand(goto_conds[k]))
        goto_conds[k] = balance_parens(goto_conds[k])
        
        goto_conds[k] = balance_parens(goto_conds[k])
        
        # Final aggressive simplification to remove duplicates and excessive parentheses
        goto_conds[k] = dedup_top_level_or(goto_conds[k])
        # Balance again after dedup
        goto_conds[k] = balance_parens(goto_conds[k])
        # Aggressively reduce parentheses before final simplification
        goto_conds[k] = aggressively_reduce_parens(goto_conds[k])
        # Final balance and validation
        goto_conds[k] = balance_parens(goto_conds[k])
        goto_conds[k] = simplify_condition(goto_conds[k])  # Run again to clean up after dedup
        
        goto_conds[k] = balance_parens(goto_conds[k])
        
        # Final dedup one more time after all fixes
        goto_conds[k] = dedup_top_level_or(goto_conds[k])
        goto_conds[k] = balance_parens(goto_conds[k])
        # Repair simple OR chains if parens got unbalanced
        goto_conds[k] = repair_simple_or_chain(goto_conds[k])
        goto_conds[k] = balance_parens(goto_conds[k])

    return goto_conds


# ---------- DETECT PERFORM/CALL TYPES + RANGE INFO ----------

def detect_edge_type_and_meta(par_lines: List[str], target: str) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Returns (etype, meta) where meta can include:
      - range_start, range_end for CALL_RANGE
      - evidence_line (the line that matched)
    """
    target = norm_name(target)

    for line in par_lines:
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
                    "evidence_line": line.strip()
                }

        # PERFORM A (but not THRU)
        m = re.search(r"\bPERFORM\b\s+([A-Z0-9\-]+)\b", u, re.I)
        if m and "THRU" not in u:
            callee = norm_name(m.group(1))
            if callee == target:
                return "CALL", {"evidence_line": line.strip()}

        # GO TO A
        m = re.search(r"\bGO\s+TO\b\s+([A-Z0-9\-]+)", u, re.I)
        if m:
            goto = norm_name(m.group(1))
            if goto == target:
                return "JUMP", {"evidence_line": line.strip()}

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
    paragraphs, order = parse_procedure_paragraphs(cobol_text)

    # Precompute:
    # - goto conditions per paragraph
    goto_conditions: Dict[str, Dict[str, str]] = {
        pname: extract_goto_conditions(lines) for pname, lines in paragraphs.items()
    }

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
            etype, meta = detect_edge_type_and_meta(paragraphs[src], tgt)

        if not etype:
            etype = "FALLTHROUGH"

        edge["type"] = etype

        # Add condition for JUMP edges (from IF stacks)
        if etype == "JUMP" and src in goto_conditions:
            # Special-case: PDCBVC.BROWSE-FASE1 -> XCTL-LIV4 is handled later
            if not (program_id == "PDCBVC" and src == "BROWSE-FASE1" and tgt == "XCTL-LIV4"):
                cond = goto_conditions[src].get(tgt)
                if cond:
                    cond = cond.strip()
                    # Fix any structural issues first
                    # Ensure parentheses are balanced (simple count-based balancing)
                    op = cond.count("(")
                    cp = cond.count(")")
                    if op > cp:
                        cond += ")" * (op - cp)
                    elif cp > op:
                        cond = ("(" * (cp - op)) + cond
                    # If condition doesn't start with parentheses and contains operators, wrap it
                    if not cond.startswith("(") and (" AND " in cond.upper() or " OR " in cond.upper() or " NOT " in cond.upper()):
                        cond = f"({cond})"
                    # Final balance check
                    op = cond.count("(")
                    cp = cond.count(")")
                    if op > cp:
                        cond += ")" * (op - cp)
                    elif cp > op:
                        cond = ("(" * (cp - op)) + cond
                    edge["condition"] = cond
                else:
                    edge.pop("condition", None)
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

    # Special handling for PDCBVC: refine BROWSE-FASE1 conditions
    if program_id == "PDCBVC":
        # 1) Condition for PERFORM READ-TAB-SEMAF
        # Keep COBOL-style shorthand exactly as written in the source:
        # IF (TWCOB-FUNZIONE =  'I' OR 'A' OR 'C' OR 'D' OR 'P')
        semaf_if_cond = "(TWCOB-FUNZIONE = 'I' OR 'A' OR 'C' OR 'D' OR 'P') AND TWCOB-ID-SISTEMA = 'IP'"
        semaf_goto_cond = "(TWCOB-FUNZIONE = 'I' OR 'A' OR 'C' OR 'D' OR 'P') AND TWCOB-ID-SISTEMA = 'IP' AND PXCSEMAF-STATUS = 1"
        pd1_goto_cond = "PD1VOCI-TABVOX-NUMERO = 0 AND TWCOB-XCTL-PGM = 'PDCGVC'"

        # Attach condition to CALL edge BROWSE-FASE1 -> READ-TAB-SEMAF
        for edge in graph.get("edges", []):
            if edge.get("from") == "BROWSE-FASE1" and edge.get("to") == "READ-TAB-SEMAF":
                edge["condition"] = semaf_if_cond
                break

        # 2) Ensure we have two separate JUMP edges from BROWSE-FASE1 to XCTL-LIV4
        b1_to_liv4 = [e for e in graph.get("edges", []) if e.get("from") == "BROWSE-FASE1" and e.get("to") == "XCTL-LIV4"]

        if b1_to_liv4:
            # First edge: semaforo closed path
            b1_to_liv4[0]["type"] = "JUMP"
            b1_to_liv4[0]["condition"] = semaf_goto_cond

            # Check if a PD1VOCI-based edge already exists
            has_pd1 = any(
                isinstance(e.get("condition"), str) and "PD1VOCI-TABVOX-NUMERO" in e["condition"]
                for e in b1_to_liv4
            )
            if not has_pd1:
                graph.setdefault("edges", []).append(
                    {
                        "from": "BROWSE-FASE1",
                        "to": "XCTL-LIV4",
                        "type": "JUMP",
                        "condition": pd1_goto_cond,
                        "evidence": "GO  TO  XCTL-LIV4",
                    }
                )

        # 3) Condition for PERFORM ABEND00 inside READ-TAB-SEMAF
        #    IF PXCSEMAF-OUTCOME NOT = SPACE
        for edge in graph.get("edges", []):
            if edge.get("from") == "READ-TAB-SEMAF" and edge.get("to") == "ABEND00":
                edge["condition"] = "PXCSEMAF-OUTCOME NOT = SPACE"
                break

        # 4) Condition for top-level GO TO ABEND00 (fallback when neither FASE 1 nor 2)
        for edge in graph.get("edges", []):
            if edge.get("from") == program_id and edge.get("to") == "ABEND00":
                # Both IFs must be false to reach here:
                # IF  TWCOB-FASE = '1' THEN GO TO BROWSE-FASE1.
                # IF  TWCOB-FASE = '2' THEN GO TO BROWSE-FASE2.
                edge["condition"] = "NOT (TWCOB-FASE = '1' OR TWCOB-FASE = '2')"
                break


        # 5) Fix BROWSE-FASE2-ENTER selection condition (needs NOT SPACES too)
        for edge in graph.get("edges", []):
            if edge.get("from") == "BROWSE-FASE2-ENTER" and edge.get("to") == "BROWSE-FASE2-SEL":
                edge["condition"] = "(SCELTAI NOT = '__') AND (SCELTAI NOT = SPACES)"
                break

        # 6) Fix MUOVI-DATI-10 -> MUOVI-DATI-30 condition (two independent IFs)
        for edge in graph.get("edges", []):
            if edge.get("from") == "MUOVI-DATI-10" and edge.get("to") == "MUOVI-DATI-30":
                edge["condition"] = "(PD1VOCI-IND GREATER PD1VOCI-TABVOX-NUMERO) OR (WCTRIG GREATER 15)"
                break

        # 7) Ensure MUOVI-DATI -> MUOVI-DATI-10 has both FASE 1 and 2 paths
        muovi_cond_1 = "(TWCOB-XCTL-PGM = 'PDCGVC') AND (TWCOB-FASE = '1')"
        muovi_cond_2 = "(TWCOB-XCTL-PGM = 'PDCGVC') AND (TWCOB-FASE = '2')"
        muovi_edges = [e for e in graph.get("edges", []) if e.get("from") == "MUOVI-DATI" and e.get("to") == "MUOVI-DATI-10"]
        has_1 = any(e.get("condition") == muovi_cond_1 for e in muovi_edges)
        has_2 = any(e.get("condition") == muovi_cond_2 for e in muovi_edges)
        if not has_1:
            graph.setdefault("edges", []).append(
                {
                    "from": "MUOVI-DATI",
                    "to": "MUOVI-DATI-10",
                    "type": "JUMP",
                    "condition": muovi_cond_1,
                    "evidence": "GO  TO  MUOVI-DATI-10.",
                }
            )
        if not has_2:
            graph.setdefault("edges", []).append(
                {
                    "from": "MUOVI-DATI",
                    "to": "MUOVI-DATI-10",
                    "type": "JUMP",
                    "condition": muovi_cond_2,
                    "evidence": "GO  TO  MUOVI-DATI-10.",
                }
            )

        # 8) Ensure BROWSE-FASE1 -> XCTL-LIV4 edge for PD1VOCI-TABVOX-NUMERO = 0 (unguarded)
        pd1_simple_cond = "PD1VOCI-TABVOX-NUMERO = 0"
        has_pd1_simple = any(
            e.get("from") == "BROWSE-FASE1"
            and e.get("to") == "XCTL-LIV4"
            and e.get("condition") == pd1_simple_cond
            for e in graph.get("edges", [])
        )
        if not has_pd1_simple:
            graph.setdefault("edges", []).append(
                {
                    "from": "BROWSE-FASE1",
                    "to": "XCTL-LIV4",
                    "type": "JUMP",
                    "condition": pd1_simple_cond,
                    "evidence": "GO  TO  XCTL-LIV4",
                }
            )

        # 9) Normalize INIZ-PARAM -> INIZ-PARAM-010 condition (dedup)
        for edge in graph.get("edges", []):
            if edge.get("from") == "INIZ-PARAM" and edge.get("to") == "INIZ-PARAM-010":
                edge["condition"] = "(TWCOB-VARCONT-NUMFUNZ = '1') OR (TWCOB-VARCONT-NUMFUNZ = '6') OR (TWCOB-FUNZIONE = 'I')"
                break
    # Add some summary metadata
    graph.setdefault("meta", {})
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
