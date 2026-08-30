#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


MOVE_LITERAL_RE = re.compile(
    r"\bMOVE\s+(?P<literal>'[^']*'|\"[^\"]*\"|[+-]?\d+(?:\.\d+)?)\s+TO\s+(?P<target>[A-Z0-9-]+)\b",
    re.IGNORECASE,
)


def make_id(text: str) -> str:
    return hashlib.blake2b(text.encode("utf-8"), digest_size=8).hexdigest()


def normalize_literal(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
        return raw[1:-1]
    return raw


def load_variables(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("variables"), list):
        return data["variables"]
    if isinstance(data, list):
        return data
    raise SystemExit(f"{path} must contain a variable list or dataflow.used_variables object")


# BMS builds a symbolic map by emitting a family of fields per screen field:
# a length, a flag, an attribute, and an input/output value. A copybook that
# declares such families is a map copybook whatever it is named, so the map
# does not have to be identified by name for each program.
_BMS_SUFFIXES = "LFAIO"


def bms_origins(variables: list[dict[str, Any]]) -> set[str]:
    grouped: dict[str, set[str]] = {}
    for variable in variables:
        origin = str(variable.get("origin") or "").upper()
        name = str(variable.get("variable") or "").upper()
        if origin.startswith("COPY:") and name:
            grouped.setdefault(origin, set()).add(name)

    detected: set[str] = set()
    for origin, names in grouped.items():
        stems: dict[str, set[str]] = {}
        for name in names:
            if len(name) > 1 and name[-1] in _BMS_SUFFIXES:
                stems.setdefault(name[:-1], set()).add(name[-1])
        if any(len(suffixes) >= 2 for suffixes in stems.values()):
            detected.add(origin)
    return detected


_CALL_ARGUMENT_RE = re.compile(
    r"(?:\bUSING\b|\bCOMMAREA\s*\()\s*(?P<args>[^)]+)", re.IGNORECASE
)


def commarea_prefixes(variables: list[dict[str, Any]]) -> set[str]:
    """Prefixes of fields belonging to a call interface.

    Two structural signals, because either alone misses real cases. A commarea
    copybook is named after the interface it carries, so its fields share the
    member name as a prefix; and an area named in a CALL ... USING or an
    EXEC CICS COMMAREA is a call interface whether or not its copybook was
    supplied with the program. The second signal is what covers an interface
    whose copybook is absent, where every field is left with no origin at all.
    """
    prefixes: set[str] = set()

    for variable in variables:
        origin = str(variable.get("origin") or "").upper()
        name = str(variable.get("variable") or "").upper()
        if origin.startswith("COPY:") and "-" in name:
            member = origin.split(":", 1)[1]
            if member and name.startswith(member + "-"):
                prefixes.add(member + "-")

    for variable in variables:
        evidence = variable.get("evidence") or {}
        for kind in ("write_sites", "read_sites", "read_write_sites"):
            for site in evidence.get(kind) or []:
                statement = str(site.get("statement") or "").upper()
                for match in _CALL_ARGUMENT_RE.finditer(statement):
                    for argument in re.findall(r"[A-Z][A-Z0-9-]*", match.group("args")):
                        if "-" in argument:
                            prefixes.add(argument.split("-", 1)[0] + "-")
    return prefixes


def classify_target(
    variable: dict[str, Any],
    map_origins: set[str],
    call_prefixes: set[str],
) -> dict[str, bool]:
    target = str(variable.get("variable") or "").upper()
    origin = str(variable.get("origin") or "").upper()
    controls_flow = bool(variable.get("controls_flow"))
    return {
        "controls_flow": controls_flow,
        "screen_or_map_field": origin in map_origins
        or re.match(r"^M\d[A-Z0-9-]+[A-Z]$", target) is not None,
        "call_commarea_field": any(target.startswith(prefix) for prefix in call_prefixes),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Build dataflow.literal_assignments.json from variable-use evidence")
    ap.add_argument("--input", required=True, help="Path to pdc_var_index_used.json or dataflow.used_variables.json")
    ap.add_argument("--program", required=True, help="Program name")
    ap.add_argument("--output", required=True, help="Output dataflow.literal_assignments.json path")
    args = ap.parse_args()

    assignments: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, int]] = set()

    all_variables = load_variables(Path(args.input))
    map_origins = bms_origins(all_variables)
    call_prefixes = commarea_prefixes(all_variables)

    for variable in all_variables:
        target = str(variable.get("variable") or "").upper()
        evidence = variable.get("evidence") or {}
        for site in evidence.get("write_sites") or []:
            statement = str(site.get("statement") or "").strip()
            match = MOVE_LITERAL_RE.search(statement)
            if not match:
                continue

            statement_target = match.group("target").upper()
            if target and statement_target != target:
                continue

            paragraph = str(site.get("paragraph") or "")
            line = int(site.get("line_start") or site.get("line") or 0)
            literal_raw = match.group("literal")
            key = (statement_target, literal_raw, paragraph, line)
            if key in seen:
                continue
            seen.add(key)

            flags = classify_target(variable, map_origins, call_prefixes)
            assignments.append(
                {
                    "id": make_id(f"{args.program}|{statement_target}|{literal_raw}|{paragraph}|{line}"),
                    "program": args.program,
                    "target_variable": statement_target,
                    "literal": normalize_literal(literal_raw),
                    "literal_raw": literal_raw,
                    "paragraph": paragraph,
                    "line": line or None,
                    "statement": statement,
                    "origin": variable.get("origin"),
                    **flags,
                }
            )

    assignments.sort(key=lambda item: (item.get("line") or 0, item["target_variable"], item["literal_raw"]))

    out = {
        "type": "dataflow.literal_assignments",
        "program": args.program,
        "title": f"{args.program} literal assignments",
        "embedding_text": (
            f"{args.program} literal and forced value assignments. "
            + " ".join(
                f"{a['target_variable']} gets {a['literal_raw']} in {a['paragraph']} line {a.get('line') or 'unknown'}."
                for a in assignments[:80]
            )
        ),
        "assignments": assignments,
        "meta": {
            "count": len(assignments),
            "controls_flow_count": sum(1 for a in assignments if a["controls_flow"]),
            "screen_or_map_field_count": sum(1 for a in assignments if a["screen_or_map_field"]),
            "call_commarea_field_count": sum(1 for a in assignments if a["call_commarea_field"]),
        },
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Wrote {len(assignments)} literal assignments to {output}")


if __name__ == "__main__":
    main()
