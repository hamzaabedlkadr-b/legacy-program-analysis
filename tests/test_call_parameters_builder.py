from __future__ import annotations

import importlib.util
from pathlib import Path


BUILDER_PATH = (
    Path(__file__).parents[1]
    / "artifacts/final/final_scripts/architecture.call_parameters"
    / "build_architecture_call_parameters.py"
)
SPEC = importlib.util.spec_from_file_location("call_parameters_builder", BUILDER_PATH)
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def test_tagged_comment_and_setup_lines_do_not_replace_call_location(tmp_path: Path) -> None:
    cobol = tmp_path / "PROGRAM.CBL"
    cobol.write_text(
        "       READ-TAB-SEMAF.\n"
        "mar23 * CALL SETUP STARTS HERE\n"
        "       INITIALIZE PXCSEMAF-AREA\n"
        "       MOVE 'INQUIRE' TO PXCSEMAF-REQ\n"
        "       MOVE USER-NAME TO PXCSEMAF-NAME\n"
        "       CALL PXRSEMAF USING PXCSEMAF-AREA\n"
        "       IF PXCSEMAF-OUTCOME = 'OK' CONTINUE.\n",
        encoding="utf-8",
    )
    statements = builder.load_cobol_statements(cobol)
    calls = builder.extract_calls(statements)

    assert len(calls) == 1
    assert calls[0]["target"] == "PXRSEMAF"
    assert calls[0]["paragraph"] == "READ-TAB-SEMAF"
    assert calls[0]["line_start"] == 6
    assert calls[0]["line_end"] == 6
    assert calls[0]["statement"] == "CALL PXRSEMAF USING PXCSEMAF-AREA"

    variables = {
        "PXCSEMAF-REQ": {
            "evidence": {
                "write_sites": [{"paragraph": "READ-TAB-SEMAF", "line_start": 3}],
                "read_sites": [],
            }
        },
        "PXCSEMAF-NAME": {
            "evidence": {
                "write_sites": [{"paragraph": "READ-TAB-SEMAF", "line_start": 4}],
                "read_sites": [],
            }
        },
        "PXCSEMAF-OUTCOME": {
            "evidence": {
                "write_sites": [],
                "read_sites": [{"paragraph": "READ-TAB-SEMAF", "line_start": 7}],
            }
        },
    }
    summary = builder.variable_summary("PXCSEMAF", variables, calls[0]["line_start"])
    by_name = {item["variable"]: item for item in summary}
    assert by_name["PXCSEMAF-REQ"]["writes_before_call"]
    assert by_name["PXCSEMAF-NAME"]["writes_before_call"]
    assert by_name["PXCSEMAF-OUTCOME"]["reads_after_call"]
