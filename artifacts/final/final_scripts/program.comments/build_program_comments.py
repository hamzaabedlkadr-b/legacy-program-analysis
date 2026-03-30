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

        # Track section context
        m_sec = SECTION_RE.match(up)
        if m_sec:
            current_section = m_sec.group(1).upper()
            current_para = None

        # Track paragraph context
        m = PARA_RE.match(up) if in_procedure_division else None
        if m:
            current_para = m.group(1).upper()
            procedure_paragraphs.add(current_para)

        # Full-line comment (indicator in col 7)
        if indicator in ("*", "/"):
            txt_raw = code.strip()
            txt = normalize_comment_text(txt_raw)
            if txt and not is_noise_comment(txt):
                comments.append({
                    "line": idx,
                    "section": current_section,
                    "paragraph": current_para,
                    "text": txt,
                    "text_raw": txt_raw,
                    "kind": "full_line",
                })
            else:
                filtered_out += 1
            continue

        # Inline comment using *> in code area
        if "*>".upper() in up:
            parts = code.split("*>", 1)
            txt_raw = parts[1].strip() if len(parts) > 1 else ""
            txt = normalize_comment_text(txt_raw)
            if txt and not is_noise_comment(txt):
                comments.append({
                    "line": idx,
                    "section": current_section,
                    "paragraph": current_para,
                    "text": txt,
                    "text_raw": txt_raw,
                    "kind": "inline",
                })
            else:
                filtered_out += 1

    paragraphs_with_comments = {
        str(c.get("paragraph")).upper()
        for c in comments
        if c.get("paragraph")
    }
    orphan_comments = sum(1 for c in comments if not c.get("paragraph"))

    comments_per_100_lines = 0.0
    if total_lines > 0:
        comments_per_100_lines = round((len(comments) / total_lines) * 100.0, 2)

    paragraph_coverage_pct = 0.0
    if procedure_paragraphs:
        paragraph_coverage_pct = round(
            (len(paragraphs_with_comments) / len(procedure_paragraphs)) * 100.0, 2
        )

    metrics = {
        "total_lines": total_lines,
        "total_procedure_paragraphs": len(procedure_paragraphs),
        "paragraphs_with_comments": len(paragraphs_with_comments),
        "paragraph_coverage_pct": paragraph_coverage_pct,
        "orphan_comments": orphan_comments,
        "comments_per_100_lines": comments_per_100_lines,
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


def make_comment_doc(program: str, source: str, comment: Dict, rule_index: Dict[str, List[str]],
                     var_index: Dict[str, List[str]]) -> Dict:
    line = int(comment.get("line", 0))
    section = comment.get("section")
    paragraph = comment.get("paragraph")
    kind = comment.get("kind")
    text = comment.get("text", "")

    para_key = str(paragraph or "").upper()
    rule_links = rule_index.get(para_key, []) if para_key else []
    var_links = var_index.get(para_key, []) if para_key else []

    digest = hashlib.sha1(f"{program}|{line}|{kind}|{text}".encode("utf-8")).hexdigest()[:12]
    doc_id = f"program.comment.{program}.{line}.{digest}"

    tags = [f"program:{program}", f"kind:{kind}"]
    if section:
        tags.append(f"section:{section}")
    if paragraph:
        tags.append(f"paragraph:{paragraph}")

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
        },
        "meta": {
            "source": source,
            "line": line,
            "section": section,
            "paragraph": paragraph,
            "kind": kind,
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
        rag_docs.append(make_comment_doc(args.program, str(cobol_path), c, rule_index, var_index))

    out = {
        "type": "program.comments",
        "program": args.program,
        "source": str(cobol_path),
        "count": len(comments),
        "filtered_out": filtered_out,
        "rag_doc_count": len(rag_docs),
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
        for doc in rag_docs:
            line = int(doc.get("content", {}).get("line", 0))
            doc_path = rag_out_dir / f"program.comment.L{line:06d}.json"
            doc_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] Wrote {len(rag_docs)} comment docs to {rag_out_dir}")


if __name__ == "__main__":
    main()
