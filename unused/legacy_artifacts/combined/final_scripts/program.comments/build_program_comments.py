#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional


PARA_RE = re.compile(r"^\s*([A-Z][A-Z0-9-]{1,30})\.\s*$")
SECTION_RE = re.compile(r"^\s*([A-Z][A-Z0-9-]{1,30})\s+SECTION\.\s*$")
PROCEDURE_DIV_RE = re.compile(r"^\s*PROCEDURE\s+DIVISION\.\s*$")
DIVISION_RE = re.compile(r"^\s*(IDENTIFICATION|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION\b", re.I)
COBOL_SECTION_RE = re.compile(r"^\s*([A-Z][A-Z0-9-]{1,30})\s+SECTION\b", re.I)
LEVEL_DECL_RE = re.compile(r"^\s*(01|03|05|07|09|11|13|15|17|19|66|77|88)\b")
COBOL_VERB_RE = re.compile(
    r"^\s*(COPY|MOVE|IF|ELSE|END-IF|PERFORM|CALL|EXEC\b|INITIALIZE|COMPUTE|SET|"
    r"SEARCH|READ|WRITE|REWRITE|DELETE|OPEN|CLOSE|START|ACCEPT|DISPLAY|GO\s+TO|"
    r"GOBACK|STOP\s+RUN|ADD|SUBTRACT|MULTIPLY|DIVIDE|STRING|UNSTRING|INSPECT|EVALUATE)\b",
    re.I,
)
SPACED_HEADER_RE = re.compile(r"^[A-Z](?:\s+[A-Z]){2,}$")
SINGLE_NAME_RE = re.compile(r"^[A-Z][A-Z0-9-]{2,}$")
IDENTIFIER_TOKEN_RE = re.compile(r"^[A-Z][A-Z0-9-]{1,30}$")

GENERIC_HEADER_TERMS = {
    "IDENTIFICATION DIVISION",
    "ENVIRONMENT DIVISION",
    "DATA DIVISION",
    "PROCEDURE DIVISION",
    "CONFIGURATION SECTION",
    "INPUT-OUTPUT SECTION",
    "FILE SECTION",
    "WORKING-STORAGE SECTION",
    "LOCAL-STORAGE SECTION",
    "LINKAGE SECTION",
    "SCREEN SECTION",
    "REPORT SECTION",
    "COSTANTI",
    "VARIABILI",
    "MAPPE",
    "M A P P E",
    "SQL AREA",
    "S Q L A R E A",
}

DESCRIPTIVE_HEADER_PREFIXES = (
    "AREA ",
    "AREA DI ",
    "AREA COMUNICAZIONE ",
    "INIZIO ",
    "VISUALIZZAZIONE ",
    "CALCOLO ",
    "PREPARAZIONE ",
    "IMPOSTA ",
    "IMPOSTAZIONE ",
    "TRASFERIMENTO ",
    "LETTURA ",
    "LINK ",
    "INVIO ",
    "RESET ",
    "SALVATAGGIO ",
    "INDIRIZZA ",
)


def normalize_line_fixed_format(raw: str):
    """
    COBOL fixed format:
      cols 1-6: sequence
      col 7: indicator
      cols 8-72: code
    Returns (code, indicator)
    """
    line = raw.rstrip("\n")
    if not line:
        return "", " "

    padded = line + (" " * max(0, 80 - len(line)))
    indicator = padded[6] if len(padded) > 6 else " "
    code = padded[7:72].rstrip()
    return code, indicator


def normalize_comment_text(text: str) -> str:
    s = (text or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def is_noise_comment(text: str) -> bool:
    s = (text or "").strip()
    if not s:
        return True

    # Decorative separator lines like ***** ----- ===== ____ or mixed punctuation.
    if re.fullmatch(r"[\*\-=/_.~`#]+", s):
        return True

    # If there are no letters/digits, it is almost always decorative noise.
    if not re.search(r"[A-Za-z0-9]", s):
        return True

    return False


def normalize_comment_for_classification(text: str) -> str:
    s = normalize_comment_text(text)
    s = re.sub(r"^[*/\s]+", "", s)
    s = re.sub(r"[\s*]+$", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def has_lowercase_letter(text: str) -> bool:
    return any(ch.isalpha() and ch != ch.upper() for ch in text)


def looks_like_commented_code(text: str) -> bool:
    s = normalize_comment_for_classification(text)
    if not s:
        return False

    if DIVISION_RE.match(s) or COBOL_SECTION_RE.match(s):
        return False

    score = 0

    if LEVEL_DECL_RE.match(s):
        score += 4
    if COBOL_VERB_RE.match(s):
        score += 4
    if re.match(r"^\s*(TO|FROM|INTO|BY)\b", s, re.I):
        score += 3
    if re.match(r"^\s*(FD|SD|SELECT|COPY|EXEC|PROGRAM-ID|FILE-CONTROL|EJECT|SKIP\d)\b", s, re.I):
        score += 3
    if re.search(
        r"\b(PIC|PICTURE|VALUE|COMP(?:-[1-9])?|COMP-3|BINARY|REDEFINES|OCCURS|USAGE|"
        r"INDEXED|DEPENDING|VARYING|UNTIL|ASCENDING|DESCENDING|THRU|THROUGH|"
        r"END-EXEC|END-IF|END-EVALUATE|SQLCA|CURSOR|SUPPRESS)\b",
        s,
        re.I,
    ):
        score += 2
    if re.search(r"\b(TO|FROM|INTO|BY|USING|GIVING)\b", s, re.I) and re.search(r"[A-Z0-9-]", s):
        score += 1
    if re.match(r"^[A-Z0-9-]+\.\s*$", s) and not SINGLE_NAME_RE.match(s.rstrip(".")):
        score += 1
    if s.endswith("."):
        score += 1

    return score >= 4


def looks_like_section_header(text: str) -> bool:
    s = normalize_comment_for_classification(text).upper()
    if not s:
        return False

    if s in GENERIC_HEADER_TERMS:
        return True
    if DIVISION_RE.match(s) or COBOL_SECTION_RE.match(s):
        return True
    if SPACED_HEADER_RE.match(s):
        return True

    words = [w for w in re.findall(r"[A-Z0-9-]+", s) if w]
    if 1 <= len(words) <= 2 and " ".join(words) in GENERIC_HEADER_TERMS:
        return True

    return False


def looks_like_name_or_reference(text: str) -> bool:
    s = normalize_comment_for_classification(text)
    if not s:
        return False

    if ":" in s or "/" in s or "(" in s or ")" in s:
        return False

    words = [w for w in re.findall(r"[A-Z0-9-]+", s.upper()) if w]
    if not words:
        return False

    if len(words) == 1 and IDENTIFIER_TOKEN_RE.fullmatch(words[0]) and words[0] not in GENERIC_HEADER_TERMS:
        return True

    if len(words) == 2 and all(IDENTIFIER_TOKEN_RE.fullmatch(w) for w in words) and any(
        re.search(r"[\d-]", w) for w in words
    ):
        return True

    return False


def looks_like_descriptive_header(text: str) -> bool:
    raw = normalize_comment_text(text)
    if not raw:
        return False

    stripped = raw.lstrip()
    if stripped.startswith("- ") or stripped.startswith("(") or re.match(r"^\d+\s*=", stripped):
        return False

    s = normalize_comment_for_classification(raw)
    if re.match(r"^-{2,}\s*\S", stripped):
        s = re.sub(r"^-+\s*", "", s)

    words = re.findall(r"[A-Za-z0-9'-]+", s)
    if not words or len(words) > 12:
        return False

    if has_lowercase_letter(s):
        return False

    if s.upper().startswith(DESCRIPTIVE_HEADER_PREFIXES):
        return True

    if s.endswith("."):
        return False

    if len(words) <= 8:
        return True

    return False


def classify_comment(text: str, kind: str, in_procedure_division: bool) -> Dict[str, object]:
    normalized = normalize_comment_for_classification(text)

    if looks_like_commented_code(normalized):
        return {
            "classification": "commented_out_code",
            "classification_reason": "Looks like disabled COBOL code or a data declaration.",
            "indexable": False,
            "normalized_text": normalized,
        }

    if looks_like_section_header(normalized):
        return {
            "classification": "section_header",
            "classification_reason": "Looks like a structural COBOL division, section, or banner header.",
            "indexable": False,
            "normalized_text": normalized,
        }

    if looks_like_name_or_reference(normalized):
        return {
            "classification": "name_or_reference",
            "classification_reason": "Looks like an identifier, file name, copybook name, or short reference label.",
            "indexable": False,
            "normalized_text": normalized,
        }

    if looks_like_descriptive_header(normalized):
        return {
            "classification": "descriptive_header",
            "classification_reason": "Looks like a short descriptive banner for a data area or processing step.",
            "indexable": True,
            "normalized_text": normalized,
        }

    reason = "Looks like a natural-language explanatory comment."
    if kind == "inline" and not in_procedure_division:
        reason = "Inline natural-language comment outside PROCEDURE DIVISION."

    return {
        "classification": "explanatory_comment",
        "classification_reason": reason,
        "indexable": True,
        "normalized_text": normalized,
    }


def extract_comments(cobol_path: Path) -> tuple[List[Dict], int, Dict]:
    comments = []
    current_para: Optional[str] = None
    current_section: Optional[str] = None
    in_procedure_division = False
    filtered_out = 0
    total_lines = 0
    procedure_paragraphs = set()

    for idx, raw in enumerate(cobol_path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        total_lines = idx
        code, indicator = normalize_line_fixed_format(raw)
        up = code.upper()

        if PROCEDURE_DIV_RE.match(up):
            in_procedure_division = True
            current_para = None

        m_sec = SECTION_RE.match(up)
        if m_sec:
            current_section = m_sec.group(1).upper()
            current_para = None

        m = PARA_RE.match(up) if in_procedure_division else None
        if m:
            current_para = m.group(1).upper()
            procedure_paragraphs.add(current_para)

        if indicator in ("*", "/"):
            txt_raw = code.strip()
            txt = normalize_comment_text(txt_raw)
            if txt and not is_noise_comment(txt):
                classification = classify_comment(txt, "full_line", in_procedure_division)
                comments.append({
                    "line": idx,
                    "section": current_section,
                    "paragraph": current_para,
                    "text": txt,
                    "text_raw": txt_raw,
                    "kind": "full_line",
                    "normalized_text": classification["normalized_text"],
                    "classification": classification["classification"],
                    "classification_reason": classification["classification_reason"],
                    "indexable": classification["indexable"],
                })
            else:
                filtered_out += 1
            continue

        if "*>".upper() in up:
            parts = code.split("*>", 1)
            txt_raw = parts[1].strip() if len(parts) > 1 else ""
            txt = normalize_comment_text(txt_raw)
            if txt and not is_noise_comment(txt):
                classification = classify_comment(txt, "inline", in_procedure_division)
                comments.append({
                    "line": idx,
                    "section": current_section,
                    "paragraph": current_para,
                    "text": txt,
                    "text_raw": txt_raw,
                    "kind": "inline",
                    "normalized_text": classification["normalized_text"],
                    "classification": classification["classification"],
                    "classification_reason": classification["classification_reason"],
                    "indexable": classification["indexable"],
                })
            else:
                filtered_out += 1

    paragraphs_with_comments = {
        str(c.get("paragraph")).upper()
        for c in comments
        if c.get("paragraph")
    }
    paragraphs_with_indexable_comments = {
        str(c.get("paragraph")).upper()
        for c in comments
        if c.get("paragraph") and c.get("indexable")
    }
    orphan_comments = sum(1 for c in comments if not c.get("paragraph"))
    indexable_comments = [c for c in comments if c.get("indexable")]

    classification_counts: Dict[str, int] = {}
    for c in comments:
        key = str(c.get("classification", "unknown"))
        classification_counts[key] = classification_counts.get(key, 0) + 1

    comments_per_100_lines = 0.0
    indexable_comments_per_100_lines = 0.0
    if total_lines > 0:
        comments_per_100_lines = round((len(comments) / total_lines) * 100.0, 2)
        indexable_comments_per_100_lines = round((len(indexable_comments) / total_lines) * 100.0, 2)

    paragraph_coverage_pct = 0.0
    indexable_paragraph_coverage_pct = 0.0
    if procedure_paragraphs:
        paragraph_coverage_pct = round(
            (len(paragraphs_with_comments) / len(procedure_paragraphs)) * 100.0,
            2,
        )
        indexable_paragraph_coverage_pct = round(
            (len(paragraphs_with_indexable_comments) / len(procedure_paragraphs)) * 100.0,
            2,
        )

    metrics = {
        "total_lines": total_lines,
        "total_procedure_paragraphs": len(procedure_paragraphs),
        "paragraphs_with_comments": len(paragraphs_with_comments),
        "paragraph_coverage_pct": paragraph_coverage_pct,
        "paragraphs_with_indexable_comments": len(paragraphs_with_indexable_comments),
        "indexable_paragraph_coverage_pct": indexable_paragraph_coverage_pct,
        "orphan_comments": orphan_comments,
        "comments_per_100_lines": comments_per_100_lines,
        "indexable_comments_per_100_lines": indexable_comments_per_100_lines,
        "classification_counts": classification_counts,
    }

    return comments, filtered_out, metrics


def load_json_if_exists(path: Optional[Path]):
    if not path:
        return None
    if not path.exists() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def build_rule_index(rules_doc) -> Dict[str, List[str]]:
    idx: Dict[str, List[str]] = {}
    if not isinstance(rules_doc, dict):
        return idx

    rules = rules_doc.get("rules", [])
    if not isinstance(rules, list):
        return idx

    for rule in rules:
        if not isinstance(rule, dict):
            continue
        rid = str(rule.get("id", "")).strip()
        if not rid:
            continue

        cands = set()
        scope = str(rule.get("scope", "")).strip().upper()
        if scope:
            cands.add(scope)
        ev = rule.get("evidence")
        if isinstance(ev, dict):
            frm = str(ev.get("from", "")).strip().upper()
            if frm:
                cands.add(frm)

        for key in cands:
            idx.setdefault(key, [])
            if rid not in idx[key]:
                idx[key].append(rid)

    return idx


def build_variable_index(var_doc) -> Dict[str, List[str]]:
    idx: Dict[str, List[str]] = {}
    if not isinstance(var_doc, list):
        return idx

    for item in var_doc:
        if not isinstance(item, dict):
            continue
        var_name = str(item.get("variable", "")).strip()
        if not var_name:
            continue

        for field in ("defined_in", "modified_in", "used_in"):
            vals = item.get(field, [])
            if not isinstance(vals, list):
                continue
            for p in vals:
                para = str(p).strip().upper()
                if not para:
                    continue
                idx.setdefault(para, [])
                if var_name not in idx[para]:
                    idx[para].append(var_name)

        ev = item.get("evidence")
        if isinstance(ev, dict):
            for ev_field in ("write_sites", "read_sites", "control_sites"):
                sites = ev.get(ev_field, [])
                if not isinstance(sites, list):
                    continue
                for site in sites:
                    if not isinstance(site, dict):
                        continue
                    para = str(site.get("paragraph", "")).strip().upper()
                    if not para:
                        continue
                    idx.setdefault(para, [])
                    if var_name not in idx[para]:
                        idx[para].append(var_name)

    return idx


def make_comment_doc(
    program: str,
    source: str,
    comment: Dict,
    rule_index: Dict[str, List[str]],
    var_index: Dict[str, List[str]],
) -> Dict:
    line = int(comment.get("line", 0))
    section = comment.get("section")
    paragraph = comment.get("paragraph")
    kind = comment.get("kind")
    text = comment.get("text", "")
    classification = comment.get("classification")
    indexable = bool(comment.get("indexable"))

    para_key = str(paragraph or "").upper()
    rule_links = rule_index.get(para_key, []) if para_key else []
    var_links = var_index.get(para_key, []) if para_key else []

    digest = hashlib.sha1(f"{program}|{line}|{kind}|{text}".encode("utf-8")).hexdigest()[:12]
    doc_id = f"program.comment.{program}.{line}.{digest}"

    tags = [f"program:{program}", f"kind:{kind}", f"classification:{classification}"]
    if section:
        tags.append(f"section:{section}")
    if paragraph:
        tags.append(f"paragraph:{paragraph}")
    if indexable:
        tags.append("indexable:true")

    links = {
        "business_rules": [f"business_rule.{rid}.json" for rid in rule_links],
        "variables": var_links,
    }

    emb = f"{program} comment line {line}"
    if section:
        emb += f" section {section}"
    if paragraph:
        emb += f" paragraph {paragraph}"
    emb += f". {text}"

    return {
        "id": doc_id,
        "type": "program.comment",
        "program": program,
        "title": f"{program} comment line {line}",
        "embedding_text": emb,
        "content": {
            "line": line,
            "section": section,
            "paragraph": paragraph,
            "kind": kind,
            "text": text,
            "text_raw": comment.get("text_raw"),
            "normalized_text": comment.get("normalized_text"),
            "classification": classification,
            "classification_reason": comment.get("classification_reason"),
            "indexable": indexable,
        },
        "meta": {
            "source": source,
            "line": line,
            "section": section,
            "paragraph": paragraph,
            "kind": kind,
            "classification": classification,
            "indexable": indexable,
            "tags": tags,
        },
        "links": links,
    }


def main():
    ap = argparse.ArgumentParser(description="Build program.comments.json from a COBOL file")
    ap.add_argument("--cobol", required=True, help="Path to COBOL .CBL file")
    ap.add_argument("--program", required=True, help="Program name")
    ap.add_argument("--output", required=True, help="Output program.comments.json path")
    ap.add_argument("--rules", help="Optional pdc_rules.json path used to link comments to business rules")
    ap.add_argument("--var-index", help="Optional pdc_var_index_used.json path used to link comments to variables")
    ap.add_argument("--rag-docs-dir", help="Optional output directory for per-comment RAG docs")
    args = ap.parse_args()

    cobol_path = Path(args.cobol)
    comments, filtered_out, metrics = extract_comments(cobol_path)
    rules_doc = load_json_if_exists(Path(args.rules)) if args.rules else None
    var_doc = load_json_if_exists(Path(args.var_index)) if args.var_index else None
    rule_index = build_rule_index(rules_doc)
    var_index = build_variable_index(var_doc)

    rag_docs = []
    for c in comments:
        if not c.get("indexable"):
            continue
        rag_docs.append(make_comment_doc(args.program, str(cobol_path), c, rule_index, var_index))

    classification_counts = metrics.get("classification_counts", {})
    indexable_count = sum(1 for c in comments if c.get("indexable"))

    out = {
        "type": "program.comments",
        "program": args.program,
        "source": str(cobol_path),
        "count": len(comments),
        "indexable_count": indexable_count,
        "non_indexable_count": len(comments) - indexable_count,
        "filtered_out": filtered_out,
        "rag_doc_count": len(rag_docs),
        "classification_counts": classification_counts,
        "metrics": metrics,
        "comments": comments,
        "rag_documents": rag_docs,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Wrote {out_path}")

    if args.rag_docs_dir:
        rag_out_dir = Path(args.rag_docs_dir)
        rag_out_dir.mkdir(parents=True, exist_ok=True)
        for stale_doc in rag_out_dir.glob("program.comment.L*.json"):
            stale_doc.unlink()
        for doc in rag_docs:
            line = int(doc.get("content", {}).get("line", 0))
            doc_path = rag_out_dir / f"program.comment.L{line:06d}.json"
            doc_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] Wrote {len(rag_docs)} comment docs to {rag_out_dir}")


if __name__ == "__main__":
    main()
