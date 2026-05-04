#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


PARAGRAPH_RE = re.compile(r"^\s*([A-Z0-9][A-Z0-9-]*)\.\s*$")
CALL_RE = re.compile(r"\bCALL\s+(?P<target>'[^']+'|\"[^\"]+\"|[A-Z0-9-]+)\s+USING\s+(?P<using>.+?)(?:\.|$)", re.IGNORECASE)
CICS_RE = re.compile(r"\bEXEC\s+CICS\s+(?P<op>LINK|XCTL)\b(?P<body>.*?)\bEND-EXEC\b", re.IGNORECASE | re.DOTALL)
PROGRAM_RE = re.compile(r"\bPROGRAM\s*\(\s*(?P<target>'[^']+'|\"[^\"]+\"|[A-Z0-9-]+)\s*\)", re.IGNORECASE)
COMMAREA_RE = re.compile(r"\bCOMMAREA\s*\(\s*(?P<commarea>[A-Z0-9-]+)\s*\)", re.IGNORECASE)
LENGTH_RE = re.compile(r"\bLENGTH\s*\(\s*(?P<length>[A-Z0-9-]+|\d+)\s*\)", re.IGNORECASE)


KNOWN_COMMAREA_PREFIXES = {
    "WPD1VOCI": "PD1VOCI",
    "WPD1FS00": "PD1FS00",
    "WPDRUTI01": "PDRUTI01",
    "PXCSEMAF-AREA": "PXCSEMAF",
}

NON_PARAGRAPH_WORDS = {
    "END-IF",
    "END-EXEC",
    "EXIT",
    "EJECT",
    "SKIP1",
    "SKIP2",
    "SKIP3",
}


def make_id(text: str) -> str:
    return hashlib.blake2b(text.encode("utf-8"), digest_size=8).hexdigest()


def clean_target(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
        return raw[1:-1]
    return raw


def strip_sequence(line: str) -> str:
    return line.rstrip("\n")


def load_cobol_statements(path: Path) -> list[dict[str, Any]]:
    statements: list[dict[str, Any]] = []
    current_paragraph = ""
    buffer: list[str] = []
    start_line = 0

    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        line = strip_sequence(raw_line)
        if re.match(r"^\s*(\*|/)", line):
            continue

        paragraph_match = PARAGRAPH_RE.match(line)
        if paragraph_match and paragraph_match.group(1).upper() not in NON_PARAGRAPH_WORDS:
            current_paragraph = paragraph_match.group(1)
            continue

        text = line.strip()
        if not text:
            continue
        if re.fullmatch(r"SKIP\d*|EJECT", text, re.IGNORECASE):
            continue

        if not buffer:
            start_line = line_no
        buffer.append(text)
        joined = " ".join(buffer)

        if "EXEC CICS" in joined.upper():
            if "END-EXEC" not in joined.upper():
                continue
        elif re.search(r"\bCALL\s+('[^']+'|\"[^\"]+\"|[A-Z0-9-]+)\s+USING\b", joined, re.IGNORECASE):
            pass
        elif not joined.rstrip().endswith("."):
            continue

        statements.append(
            {
                "paragraph": current_paragraph,
                "line_start": start_line,
                "line_end": line_no,
                "statement": re.sub(r"\s+", " ", joined).strip(),
            }
        )
        buffer = []
        start_line = 0

    return statements


def load_variables(path: Path | None) -> dict[str, dict[str, Any]]:
    if not path:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    variables = data.get("variables") if isinstance(data, dict) else data
    if not isinstance(variables, list):
        return {}
    return {str(v.get("variable") or "").upper(): v for v in variables if isinstance(v, dict)}


def extract_calls(statements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for statement in statements:
        text = statement["statement"]

        for match in CICS_RE.finditer(text):
            body = match.group("body")
            program = PROGRAM_RE.search(body)
            if not program:
                continue
            commarea = COMMAREA_RE.search(body)
            length = LENGTH_RE.search(body)
            calls.append(
                {
                    **statement,
                    "call_type": f"CICS{match.group('op').upper()}",
                    "target": clean_target(program.group("target")),
                    "parameters": [commarea.group("commarea").upper()] if commarea else [],
                    "commarea": commarea.group("commarea").upper() if commarea else None,
                    "length": length.group("length").upper() if length else None,
                }
            )

        call_match = CALL_RE.search(text)
        if call_match:
            using = [
                token.strip().rstrip(".").upper()
                for token in re.split(r"\s+", call_match.group("using"))
                if token.strip() and token.strip().upper() not in {"BY", "REFERENCE", "CONTENT", "VALUE"}
            ]
            calls.append(
                {
                    **statement,
                    "call_type": "CALL",
                    "target": clean_target(call_match.group("target")).upper(),
                    "parameters": using,
                    "commarea": None,
                    "length": None,
                }
            )

    return calls


def parameter_prefix(parameter: str) -> str:
    parameter = parameter.upper()
    if parameter in KNOWN_COMMAREA_PREFIXES:
        return KNOWN_COMMAREA_PREFIXES[parameter]
    return parameter


def variable_summary(prefix: str, variables: dict[str, dict[str, Any]], call_line: int) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for name, variable in sorted(variables.items()):
        if name != prefix and not name.startswith(prefix + "-"):
            continue
        evidence = variable.get("evidence") or {}
        writes = [
            site
            for site in evidence.get("write_sites") or []
            if int(site.get("line_start") or site.get("line") or 0) <= call_line
        ]
        reads = [
            site
            for site in evidence.get("read_sites") or []
            if int(site.get("line_start") or site.get("line") or 0) >= call_line
        ]
        if not writes and not reads:
            continue
        result.append(
            {
                "variable": name,
                "origin": variable.get("origin"),
                "controls_flow": bool(variable.get("controls_flow")),
                "writes_before_call": writes[-5:],
                "reads_after_call": reads[:5],
            }
        )
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="Build architecture.call_parameters.json from COBOL and variable evidence")
    ap.add_argument("--cobol", required=True, help="Path to COBOL source")
    ap.add_argument("--program", required=True, help="Program name")
    ap.add_argument("--variables", help="Path to pdc_var_index_used.json or dataflow.used_variables.json")
    ap.add_argument("--output", required=True, help="Output architecture.call_parameters.json path")
    args = ap.parse_args()

    statements = load_cobol_statements(Path(args.cobol))
    variables = load_variables(Path(args.variables)) if args.variables else {}
    calls = extract_calls(statements)

    enriched: list[dict[str, Any]] = []
    for call in calls:
        parameter_details = []
        for parameter in call["parameters"]:
            prefix = parameter_prefix(parameter)
            parameter_details.append(
                {
                    "parameter": parameter,
                    "field_prefix": prefix,
                    "variables": variable_summary(prefix, variables, int(call["line_start"])),
                }
            )
        enriched.append(
            {
                "id": make_id(f"{args.program}|{call['target']}|{call['line_start']}|{call['statement']}"),
                "program": args.program,
                "caller": args.program,
                "target": call["target"],
                "call_type": call["call_type"],
                "paragraph": call["paragraph"],
                "line_start": call["line_start"],
                "line_end": call["line_end"],
                "statement": call["statement"],
                "parameters": call["parameters"],
                "commarea": call["commarea"],
                "length": call["length"],
                "parameter_details": parameter_details,
            }
        )

    out = {
        "type": "architecture.call_parameters",
        "program": args.program,
        "title": f"{args.program} call parameters",
        "embedding_text": (
            f"{args.program} outgoing call parameters. "
            + " ".join(
                f"{c['target']} via {c['call_type']} uses {', '.join(c['parameters']) or 'no explicit parameter'} "
                f"in {c['paragraph']} line {c['line_start']}."
                for c in enriched
            )
        ),
        "calls": enriched,
        "meta": {
            "count": len(enriched),
            "with_parameters": sum(1 for c in enriched if c["parameters"]),
        },
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Wrote {len(enriched)} call parameter records to {output}")


if __name__ == "__main__":
    main()
