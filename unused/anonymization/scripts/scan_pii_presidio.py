#!/usr/bin/env python3
"""Scan text/code files for PII and create JSON plus HTML reports."""

from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider


TEXT_EXTENSIONS = {
    ".cbl",
    ".cpy",
    ".txt",
    ".csv",
    ".json",
    ".xml",
    ".md",
    ".log",
    ".sql",
    ".dat",
}

DEFAULT_ENTITIES = [
    "PERSON",
    "WATCHLIST_PERSON",
    "IBAN_CODE",
    "IT_FISCAL_CODE",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "LOCATION",
    "COBOL_NAME_LITERAL",
    "COBOL_KEY_VALUE_NAME",
    "COBOL_COMMENT_NAME",
    "COBOL_PII_FIELD",
    "IBAN_LIKE",
]

ENTITY_PRIORITY = {
    "IT_FISCAL_CODE": 100,
    "IBAN_CODE": 95,
    "EMAIL_ADDRESS": 90,
    "PHONE_NUMBER": 85,
    "COBOL_NAME_LITERAL": 80,
    "COBOL_KEY_VALUE_NAME": 78,
    "COBOL_COMMENT_NAME": 76,
    "COBOL_PII_FIELD": 75,
    "IBAN_LIKE": 70,
    "WATCHLIST_PERSON": 65,
    "PERSON": 50,
    "LOCATION": 40,
}

COBOL_KEYWORDS = {
    "CALL",
    "COMP",
    "DISPLAY",
    "ELSE",
    "END",
    "EVALUATE",
    "FD",
    "GO",
    "IF",
    "MOVE",
    "NOT",
    "PERFORM",
    "PIC",
    "SECTION",
    "SKIP1",
    "SKIP2",
    "THEN",
    "TO",
    "USING",
    "VALUE",
    "WHEN",
}

NAME_CONTEXT_WORDS = {
    "A",
    "AVVISARE",
    "CHIAMATE",
    "CHIEDERE",
    "COMPLETATA",
    "CON",
    "CONSEGNATI",
    "CONTATTARE",
    "CONTROLLARE",
    "CREATED",
    "CREATE",
    "CREATE",
    "DA",
    "DI",
    "GESTITA",
    "INSERITI",
    "MANDARE",
    "NOTIFICARE",
    "O",
    "PER",
    "REFERENTE",
    "RESPONSABILE",
    "SEGNALARE",
    "VALIDATO",
    "VISTO",
}

COMMENT_STOPWORDS = {
    "AGGIORNATA",
    "AGGIUNTA",
    "ANAGRAFICA",
    "APRE",
    "AUTORIZZAZIONE",
    "AVVENUTA",
    "AVVISO",
    "CHIUSURA",
    "CLIENTE",
    "COMPLESSO",
    "CONFIGURATION",
    "CONTATORE",
    "CONTATORE-RECORDS",
    "CONTROLLARE",
    "CREATE",
    "CREATED",
    "CRITICO",
    "DATI",
    "DEBITO",
    "DEI",
    "DISASTER",
    "DISPONIBILE",
    "DIVISION",
    "DUBBIO",
    "ERRORE",
    "FALLIMENTO",
    "FILE",
    "FISCALE",
    "FLUSSO",
    "GRAVE",
    "GRUPPO",
    "INPUT",
    "INGEGNER",
    "INTERVENTO",
    "INIZIATA",
    "LISTA",
    "LOGICA",
    "MAIL",
    "MANUTENZIONE",
    "MANUALMENTE",
    "NELL",
    "OUTPUT",
    "OPERATORE",
    "OPERATORE-LOG",
    "OTTOBRE",
    "PAGAMENTI",
    "POSSIBILE",
    "PRIORITA",
    "PRINCIPALE",
    "PROBLEMA",
    "PROCEDURA",
    "PROCESSO",
    "PROGRAMMA",
    "PROGETTO",
    "PRONTO",
    "RECOVERY",
    "RECORD",
    "REFERENTI",
    "RELAZIONE",
    "REPORT",
    "RIPRISTINO",
    "RISULTATI",
    "SCARTI",
    "SEZIONE",
    "SISTEMA",
    "STATO",
    "STRUTTURE",
    "SUBITO",
    "SULLA",
    "TABELLA",
    "TEAM",
    "TECNICO",
    "TOTALE",
    "UTENTE",
    "UTENTI",
    "VALIDATO",
    "VARIABILI",
    "VANNO",
    "QUALSIASI",
    "SENZA",
}


@dataclass(frozen=True)
class Finding:
    file: str
    entity_type: str
    score: float
    start: int
    end: int
    line: int
    column: int
    text: str
    context: str


def load_watchlist(paths: list[Path]) -> list[str]:
    names: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        for line in read_text(path).splitlines():
            value = line.strip()
            if not value or value.startswith("#"):
                continue
            names.append(value)
    return sorted(set(names), key=len, reverse=True)


def iter_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    return [
        path
        for path in input_path.rglob("*")
        if path.is_file() and (path.suffix.lower() in TEXT_EXTENSIONS or not path.suffix)
    ]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def build_analyzer() -> AnalyzerEngine:
    nlp_config = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "it", "model_name": "it_core_news_sm"}],
    }
    nlp_engine = NlpEngineProvider(nlp_configuration=nlp_config).create_engine()
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["it"])

    analyzer.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="COBOL_NAME_LITERAL",
            supported_language="it",
            name="COBOL name literal recognizer",
            patterns=[
                Pattern(
                    name="move literal to name field",
                    regex=(
                        r"\bMOVE\s+'[^\r\n']{2,80}'\s+TO\s+"
                        r"[\w-]*(?:^|-)COGNOME\b|"
                        r"\bMOVE\s+'[^\r\n']{2,80}'\s+TO\s+"
                        r"[\w-]*(?:CLIENTE-NOME|OPER-NOME|RICHIEDENTE-NOME|NOME-RICHIEDENTE|NOMINATIVO)[\w-]*\b"
                    ),
                    score=0.85,
                ),
                Pattern(
                    name="value literal in name field",
                    regex=(
                        r"\b[\w-]*(?:^|-)COGNOME\b\s+PIC\b[^\r\n]{0,80}\bVALUE\s+'[^\r\n']{2,80}'|"
                        r"\b[\w-]*(?:CLIENTE-NOME|OPER-NOME|RICHIEDENTE-NOME|NOME-RICHIEDENTE|NOMINATIVO)[\w-]*"
                        r"\s+PIC\b[^\r\n]{0,80}\bVALUE\s+'[^\r\n']{2,80}'"
                    ),
                    score=0.8,
                ),
            ],
        )
    )
    analyzer.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="COBOL_KEY_VALUE_NAME",
            supported_language="it",
            name="COBOL key-value name recognizer",
            patterns=[
                Pattern(
                    name="name inside string literal",
                    regex=r"\b(?:NOME|COGNOME|NOMINATIVO)\s*=\s*[A-Za-zÀ-ÿ][^'\r\n]{1,60}",
                    score=0.82,
                )
            ],
        )
    )
    analyzer.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="IBAN_LIKE",
            supported_language="it",
            name="IBAN-like recognizer for synthetic or checksum-invalid values",
            patterns=[
                Pattern(
                    name="iban shaped token",
                    regex=r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b",
                    score=0.7,
                )
            ],
        )
    )
    analyzer.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="COBOL_PII_FIELD",
            supported_language="it",
            name="COBOL PII field recognizer",
            patterns=[
                Pattern(
                    name="field names likely to carry PII",
                    regex=(
                        r"\b[\w-]*(?:NOME|COGNOME|NOMINATIVO|CODICE-FISCALE|"
                        r"COD-FISC|FISCAL|IBAN|EMAIL|MATRICOLA|CODDIP)[\w-]*\b"
                    ),
                    score=0.55,
                )
            ],
        )
    )
    return analyzer


def line_column(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    last_newline = text.rfind("\n", 0, offset)
    column = offset + 1 if last_newline == -1 else offset - last_newline
    return line, column


def context_for(text: str, start: int, end: int, radius: int = 80) -> str:
    prefix_start = max(0, start - radius)
    suffix_end = min(len(text), end + radius)
    return text[prefix_start:start] + "[[" + text[start:end] + "]]" + text[end:suffix_end]


def trim_span(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def is_probable_cobol_false_person(value: str) -> bool:
    normalized = " ".join(value.replace("\r", " ").replace("\n", " ").split())
    upper = normalized.upper()
    if not normalized:
        return True
    if "-" in normalized:
        return True
    if "'" in normalized or "=" in normalized:
        return True
    words = upper.split()
    if any(word in COBOL_KEYWORDS for word in words):
        return True
    if any(char.isdigit() for char in normalized):
        return True
    if normalized.isupper() and len(words) <= 3:
        return True
    return False


def remove_overlaps(findings: list[Finding]) -> list[Finding]:
    ordered = sorted(
        findings,
        key=lambda item: (
            item.file,
            item.start,
            -ENTITY_PRIORITY.get(item.entity_type, 0),
            -(item.end - item.start),
        ),
    )
    kept: list[Finding] = []
    for finding in ordered:
        overlaps = [
            existing
            for existing in kept
            if existing.file == finding.file
            and not (finding.end <= existing.start or finding.start >= existing.end)
        ]
        if not overlaps:
            kept.append(finding)
            continue
        best_overlap = max(
            overlaps,
            key=lambda item: (ENTITY_PRIORITY.get(item.entity_type, 0), item.end - item.start),
        )
        if ENTITY_PRIORITY.get(finding.entity_type, 0) > ENTITY_PRIORITY.get(best_overlap.entity_type, 0):
            kept = [item for item in kept if item not in overlaps]
            kept.append(finding)
    return sorted(kept, key=lambda item: (item.file, item.start, item.end))


def scan_file(analyzer: AnalyzerEngine, path: Path, root: Path, entities: list[str]) -> list[Finding]:
    text = read_text(path)
    results = analyzer.analyze(text=text, language="it", entities=entities)
    rel_path = str(path.relative_to(root) if root.is_dir() else path.name)
    findings: list[Finding] = []
    for result in results:
        start, end = trim_span(text, result.start, result.end)
        if start >= end:
            continue
        value = text[start:end]
        if result.entity_type == "LOCATION" and re.match(r"(?i)^VALUE\s+'", value):
            continue
        if result.entity_type == "PERSON" and is_probable_cobol_false_person(value):
            continue
        line, column = line_column(text, start)
        findings.append(
            Finding(
                file=rel_path,
                entity_type=result.entity_type,
                score=float(result.score),
                start=start,
                end=end,
                line=line,
                column=column,
                text=value,
                context=context_for(text, start, end),
            )
        )
    return findings


def scan_watchlist_file(path: Path, root: Path, watchlist: list[str]) -> list[Finding]:
    if not watchlist:
        return []
    text = read_text(path)
    rel_path = str(path.relative_to(root) if root.is_dir() else path.name)
    findings: list[Finding] = []
    for name in watchlist:
        pattern = re.compile(rf"(?<![\w-]){re.escape(name)}(?![\w-])", re.IGNORECASE)
        for match in pattern.finditer(text):
            line, column = line_column(text, match.start())
            findings.append(
                Finding(
                    file=rel_path,
                    entity_type="WATCHLIST_PERSON",
                    score=1.0,
                    start=match.start(),
                    end=match.end(),
                    line=line,
                    column=column,
                    text=text[match.start() : match.end()],
                    context=context_for(text, match.start(), match.end()),
                )
            )
    return findings


def is_comment_or_message_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("*"):
        return True
    if len(line) > 6 and line[6] == "*":
        return True
    return any(keyword in line.upper() for keyword in ("DISPLAY ", " VALUE ", " ASSIGN TO ", " STRING "))


def candidate_tokens(line: str) -> list[tuple[int, str]]:
    return [
        (match.start(), match.group(0))
        for match in re.finditer(r"\b[A-ZÀ-Ý][A-ZÀ-Ý]{2,}(?:-[A-ZÀ-Ý][A-ZÀ-Ý]{2,}){0,3}\b", line)
    ]


def looks_like_name_token(token: str) -> bool:
    parts = token.split("-")
    if any(part in COBOL_KEYWORDS or part in COMMENT_STOPWORDS for part in parts):
        return False
    if token in COMMENT_STOPWORDS:
        return False
    if any(char.isdigit() for char in token):
        return False
    if len(token) < 4:
        return False
    if token.count("-") >= 3:
        return False
    return True


def has_name_context(tokens: list[tuple[int, str]], index: int) -> bool:
    _, token = tokens[index]
    if "-" in token and not any(part in COMMENT_STOPWORDS for part in token.split("-")):
        return True
    previous_words = {tokens[pos][1] for pos in range(max(0, index - 4), index)}
    next_words = {tokens[pos][1] for pos in range(index + 1, min(len(tokens), index + 3))}
    return bool((previous_words | next_words) & NAME_CONTEXT_WORDS)


def scan_cobol_comment_names(path: Path, root: Path) -> list[Finding]:
    text = read_text(path)
    rel_path = str(path.relative_to(root) if root.is_dir() else path.name)
    findings: list[Finding] = []
    offset = 0
    for line_number, line in enumerate(text.splitlines(keepends=True), start=1):
        if not is_comment_or_message_line(line):
            offset += len(line)
            continue
        tokens = candidate_tokens(line)
        for index, (column_start, token) in enumerate(tokens):
            if not looks_like_name_token(token) or not has_name_context(tokens, index):
                continue
            start = offset + column_start
            end = start + len(token)
            findings.append(
                Finding(
                    file=rel_path,
                    entity_type="COBOL_COMMENT_NAME",
                    score=0.72,
                    start=start,
                    end=end,
                    line=line_number,
                    column=column_start + 1,
                    text=text[start:end],
                    context=context_for(text, start, end),
                )
            )
        offset += len(line)
    return findings


def finding_to_dict(finding: Finding) -> dict[str, object]:
    return {
        "file": finding.file,
        "entity_type": finding.entity_type,
        "score": round(finding.score, 4),
        "line": finding.line,
        "column": finding.column,
        "text": finding.text,
        "context": finding.context,
    }


def grouped_counts(findings: list[Finding]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.entity_type] = counts.get(finding.entity_type, 0) + 1
    return dict(sorted(counts.items()))


def highlight_context(context: str) -> str:
    escaped = html.escape(context)
    escaped = escaped.replace("[[", "<mark>").replace("]]", "</mark>")
    return escaped


def render_html(findings: list[Finding], input_path: Path) -> str:
    rows = []
    for finding in findings:
        rows.append(
            "<tr>"
            f"<td>{html.escape(finding.file)}</td>"
            f"<td>{finding.line}</td>"
            f"<td>{html.escape(finding.entity_type)}</td>"
            f"<td>{finding.score:.2f}</td>"
            f"<td><code>{html.escape(finding.text)}</code></td>"
            f"<td><pre>{highlight_context(finding.context)}</pre></td>"
            "</tr>"
        )
    count_rows = [
        f"<tr><td>{html.escape(entity)}</td><td>{count}</td></tr>"
        for entity, count in grouped_counts(findings).items()
    ]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PII Scan Report</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; margin: 24px; color: #1f2933; }}
    h1 {{ margin-bottom: 4px; }}
    .meta {{ color: #5b6773; margin-bottom: 24px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; }}
    th, td {{ border: 1px solid #d7dde3; padding: 8px; vertical-align: top; }}
    th {{ background: #f3f6f8; text-align: left; }}
    code {{ white-space: nowrap; }}
    pre {{ white-space: pre-wrap; margin: 0; font-family: Consolas, monospace; font-size: 12px; }}
    mark {{ background: #ffe08a; padding: 0 2px; border-radius: 2px; }}
  </style>
</head>
<body>
  <h1>PII Scan Report</h1>
  <div class="meta">Input: <code>{html.escape(str(input_path))}</code> | Findings: {len(findings)}</div>
  <h2>Summary</h2>
  <table>
    <thead><tr><th>Entity</th><th>Count</th></tr></thead>
    <tbody>{''.join(count_rows)}</tbody>
  </table>
  <h2>Findings</h2>
  <table>
    <thead><tr><th>File</th><th>Line</th><th>Entity</th><th>Score</th><th>Text</th><th>Context</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Input file or folder to scan.")
    parser.add_argument("--out-dir", type=Path, default=Path("unused/anonymization/artifacts/pii_scan_report"))
    parser.add_argument("--entities", nargs="*", default=DEFAULT_ENTITIES)
    parser.add_argument(
        "--watchlist",
        action="append",
        type=Path,
        default=[],
        help="Text file with one known name/surname per line. Can be passed multiple times.",
    )
    parser.add_argument("--keep-overlaps", action="store_true")
    args = parser.parse_args()

    analyzer = build_analyzer()
    default_watchlist = Path("unused/anonymization/artifacts/pii_watchlist/names.txt")
    watchlist_paths = [default_watchlist] + args.watchlist
    watchlist = load_watchlist(watchlist_paths) if "PERSON" in args.entities or "WATCHLIST_PERSON" in args.entities else []
    files = iter_files(args.input)
    findings: list[Finding] = []
    for path in files:
        findings.extend(scan_file(analyzer, path, args.input, args.entities))
        findings.extend(scan_watchlist_file(path, args.input, watchlist))
        if "COBOL_COMMENT_NAME" in args.entities:
            findings.extend(scan_cobol_comment_names(path, args.input))

    if not args.keep_overlaps:
        findings = remove_overlaps(findings)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    report_json = args.out_dir / "pii_findings.json"
    report_html = args.out_dir / "pii_report.html"
    report_json.write_text(
        json.dumps([finding_to_dict(item) for item in findings], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    report_html.write_text(render_html(findings, args.input), encoding="utf-8")

    print(f"Scanned {len(files)} files.")
    print(f"Findings: {len(findings)}")
    print(f"Counts: {grouped_counts(findings)}")
    print(f"JSON: {report_json}")
    print(f"HTML: {report_html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
