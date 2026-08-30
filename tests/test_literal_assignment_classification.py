from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from typing import Any


SCRIPT = (
    Path(__file__).parents[1]
    / "artifacts/final/final_scripts/dataflow.literal_assignments"
    / "build_dataflow_literal_assignments.py"
)
SPEC = importlib.util.spec_from_file_location("literal_assignments", SCRIPT)
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def variable(name: str, origin: str | None = None, statements: list[str] | None = None) -> dict[str, Any]:
    return {
        "variable": name,
        "origin": origin,
        "evidence": {"write_sites": [{"statement": s} for s in (statements or [])]},
    }


class BmsDetectionTest(unittest.TestCase):
    """A map copybook is recognised by the shape BMS gives it, not by its name.

    BMS emits a family of fields per screen field (length, flag, attribute,
    input/output value), so a copybook declaring such families is a symbolic
    map whatever the program calls it.
    """

    def test_copybook_with_field_families_is_a_map(self) -> None:
        variables = [
            variable("SCELTAI", "COPY:ANYMAP"),
            variable("SCELTAL", "COPY:ANYMAP"),
            variable("SCELTAO", "COPY:ANYMAP"),
        ]
        self.assertEqual(builder.bms_origins(variables), {"COPY:ANYMAP"})

    def test_two_suffixes_are_enough(self) -> None:
        variables = [variable("WSMSGL", "COPY:OTHERMAP"), variable("WSMSGO", "COPY:OTHERMAP")]
        self.assertEqual(builder.bms_origins(variables), {"COPY:OTHERMAP"})

    def test_ordinary_copybook_is_not_a_map(self) -> None:
        variables = [
            variable("RECORD-CODE", "COPY:DATAREC"),
            variable("RECORD-NAME", "COPY:DATAREC"),
            variable("RECORD-TOTAL", "COPY:DATAREC"),
        ]
        self.assertEqual(builder.bms_origins(variables), set())

    def test_a_lone_field_ending_in_a_suffix_letter_is_not_a_family(self) -> None:
        # One name ending in L proves nothing; a family needs two suffixes.
        variables = [variable("TOTAL", "COPY:DATAREC"), variable("RECORD-NAME", "COPY:DATAREC")]
        self.assertEqual(builder.bms_origins(variables), set())

    def test_variables_without_a_copybook_origin_are_ignored(self) -> None:
        variables = [variable("SCELTAI", "WORKING-STORAGE"), variable("SCELTAO", None)]
        self.assertEqual(builder.bms_origins(variables), set())


class CommareaPrefixTest(unittest.TestCase):
    def test_prefix_comes_from_the_copybook_member_name(self) -> None:
        variables = [variable("SUBAREA-CODE", "COPY:SUBAREA")]
        self.assertIn("SUBAREA-", builder.commarea_prefixes(variables))

    def test_area_named_in_a_call_using_is_an_interface(self) -> None:
        """An interface whose copybook was not supplied has no origin at all,
        so the CALL statement is the only structural evidence there is."""
        variables = [variable("IFACE-AREA", None, ["CALL SUBPGM USING IFACE-AREA"])]
        self.assertIn("IFACE-", builder.commarea_prefixes(variables))

    def test_area_named_in_a_cics_commarea_is_an_interface(self) -> None:
        variables = [
            variable("LINKAREA-CODE", None, ["EXEC CICS LINK PROGRAM('P') COMMAREA(LINKAREA-BLOCK) END-EXEC"])
        ]
        self.assertIn("LINKAREA-", builder.commarea_prefixes(variables))

    def test_unrelated_statements_contribute_no_prefixes(self) -> None:
        variables = [variable("WS-COUNT", "WORKING-STORAGE", ["MOVE 1 TO WS-COUNT"])]
        self.assertEqual(builder.commarea_prefixes(variables), set())

    def test_names_without_a_hyphen_do_not_become_prefixes(self) -> None:
        variables = [variable("FLAG", None, ["CALL SUBPGM USING FLAG"])]
        self.assertEqual(builder.commarea_prefixes(variables), set())


class ClassifyTargetTest(unittest.TestCase):
    def test_map_origin_marks_a_screen_field(self) -> None:
        flags = builder.classify_target(variable("ANYFIELDO", "COPY:ANYMAP"), {"COPY:ANYMAP"}, set())
        self.assertTrue(flags["screen_or_map_field"])

    def test_non_map_origin_does_not(self) -> None:
        flags = builder.classify_target(variable("RECORD-CODE", "COPY:DATAREC"), {"COPY:ANYMAP"}, set())
        self.assertFalse(flags["screen_or_map_field"])

    def test_commarea_prefix_marks_a_call_field(self) -> None:
        flags = builder.classify_target(variable("IFACE-CODE", None), set(), {"IFACE-"})
        self.assertTrue(flags["call_commarea_field"])

    def test_a_similar_name_outside_the_group_is_not_a_call_field(self) -> None:
        flags = builder.classify_target(variable("IFACEX-CODE", None), set(), {"IFACE-"})
        self.assertFalse(flags["call_commarea_field"])


if __name__ == "__main__":
    unittest.main()
