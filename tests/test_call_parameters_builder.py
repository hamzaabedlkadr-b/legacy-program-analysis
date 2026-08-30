"""Coverage for the call-parameter / commarea extractor.

Written as unittest.TestCase deliberately. The previous version of this file
used bare pytest functions, which `python -m unittest discover` does not
collect, so the file contributed nothing to the documented test command and its
single test never ran. TestCase is collected by both runners.
"""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from typing import Any


BUILDER_PATH = (
    Path(__file__).parents[1]
    / "artifacts/final/final_scripts/architecture.call_parameters"
    / "build_architecture_call_parameters.py"
)
SPEC = importlib.util.spec_from_file_location("call_parameters_builder", BUILDER_PATH)
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class BuilderTestCase(unittest.TestCase):
    def statements(self, source: str) -> list[dict[str, Any]]:
        """Run the real file reader, so column handling is exercised too."""
        directory = Path(tempfile.mkdtemp())
        cobol = directory / "PROGRAM.CBL"
        cobol.write_text(source, encoding="utf-8")
        return builder.load_cobol_statements(cobol)

    def calls(self, source: str) -> list[dict[str, Any]]:
        return builder.extract_calls(self.statements(source))


class StatementLoadingTest(BuilderTestCase):
    def test_comment_lines_are_skipped(self) -> None:
        statements = self.statements(
            "       PARA-A.\n"
            "      * a full-line comment\n"
            "      / a page-eject comment\n"
            "           MOVE 1 TO WS-A.\n"
        )
        self.assertEqual([s["statement"] for s in statements], ["MOVE 1 TO WS-A."])

    def test_change_tag_before_the_indicator_still_reads_as_a_comment(self) -> None:
        """A source may carry a change tag in columns 1-6, so the comment
        indicator in column 7 is not the first non-space character. Testing only
        the first character merges the comment into the following statement."""
        statements = self.statements(
            "       PARA-A.\n"
            "mar23 * CALL SETUP STARTS HERE\n"
            "           MOVE 1 TO WS-A.\n"
        )
        self.assertEqual([s["statement"] for s in statements], ["MOVE 1 TO WS-A."])

    def test_compiler_directives_are_skipped(self) -> None:
        statements = self.statements(
            "       PARA-A.\n           SKIP1\n           EJECT\n           MOVE 1 TO WS-A.\n"
        )
        self.assertEqual([s["statement"] for s in statements], ["MOVE 1 TO WS-A."])

    def test_paragraph_label_is_attributed_to_following_statements(self) -> None:
        statements = self.statements(
            "       PARA-A.\n           MOVE 1 TO WS-A.\n"
            "       PARA-B.\n           MOVE 2 TO WS-B.\n"
        )
        self.assertEqual(
            [(s["paragraph"], s["statement"]) for s in statements],
            [("PARA-A", "MOVE 1 TO WS-A."), ("PARA-B", "MOVE 2 TO WS-B.")],
        )

    def test_statement_terminators_do_not_open_a_paragraph(self) -> None:
        """EXIT. and END-IF. are statements. Treating them as labels would
        reattribute everything after them to a paragraph that does not exist."""
        for terminator in ("EXIT.", "END-IF.", "END-EXEC."):
            with self.subTest(terminator=terminator):
                statements = self.statements(
                    f"       PARA-A.\n           {terminator}\n           MOVE 1 TO WS-A.\n"
                )
                self.assertEqual(statements[-1]["paragraph"], "PARA-A")

    def test_continuation_lines_are_joined_until_the_period(self) -> None:
        statements = self.statements(
            "       PARA-A.\n           MOVE WS-LONG-SOURCE\n             TO WS-LONG-TARGET.\n"
        )
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0]["statement"], "MOVE WS-LONG-SOURCE TO WS-LONG-TARGET.")
        self.assertEqual((statements[0]["line_start"], statements[0]["line_end"]), (2, 3))

    def test_exec_cics_is_joined_until_end_exec(self) -> None:
        statements = self.statements(
            "       PARA-A.\n"
            "           EXEC CICS LINK\n"
            "                PROGRAM('PDBSUB')\n"
            "                COMMAREA(WS-AREA)\n"
            "           END-EXEC.\n"
        )
        self.assertEqual(len(statements), 1)
        self.assertEqual((statements[0]["line_start"], statements[0]["line_end"]), (2, 5))
        self.assertIn("END-EXEC", statements[0]["statement"])

    def test_whitespace_is_collapsed_in_the_recorded_statement(self) -> None:
        statements = self.statements("       PARA-A.\n           MOVE   1    TO     WS-A.\n")
        self.assertEqual(statements[0]["statement"], "MOVE 1 TO WS-A.")

    def test_a_call_is_its_own_record_and_does_not_absorb_setup_lines(self) -> None:
        """Setup statements before a CALL belong in writes_before_call, not in
        the call's own statement text or line span. COBOL permits a single
        paragraph-level period, so an unterminated MOVE would otherwise buffer
        into the CALL record and move its reported line."""
        statements = self.statements(
            "       READ-TAB-SEMAF.\n"
            "           INITIALIZE PXCSEMAF-AREA\n"
            "           MOVE 'INQUIRE' TO PXCSEMAF-REQ\n"
            "           CALL PXRSEMAF USING PXCSEMAF-AREA\n"
        )
        call = [s for s in statements if s["statement"].startswith("CALL")]
        self.assertEqual(len(call), 1)
        self.assertEqual(call[0]["statement"], "CALL PXRSEMAF USING PXCSEMAF-AREA")
        self.assertEqual((call[0]["line_start"], call[0]["line_end"]), (4, 4))
        self.assertEqual(call[0]["paragraph"], "READ-TAB-SEMAF")


class CallExtractionTest(BuilderTestCase):
    def test_cics_link_captures_target_commarea_and_length(self) -> None:
        calls = self.calls(
            "       PARA-A.\n"
            "           EXEC CICS LINK PROGRAM('PDBSUB') COMMAREA(WS-AREA) LENGTH(120) END-EXEC.\n"
        )
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["call_type"], "CICSLINK")
        self.assertEqual(calls[0]["target"], "PDBSUB")
        self.assertEqual(calls[0]["commarea"], "WS-AREA")
        self.assertEqual(calls[0]["length"], "120")
        self.assertEqual(calls[0]["parameters"], ["WS-AREA"])

    def test_xctl_is_distinguished_from_link(self) -> None:
        calls = self.calls(
            "       PARA-A.\n           EXEC CICS XCTL PROGRAM('NEXTPGM') END-EXEC.\n"
        )
        self.assertEqual(calls[0]["call_type"], "CICSXCTL")
        self.assertEqual(calls[0]["target"], "NEXTPGM")

    def test_cics_without_a_program_operand_yields_no_call(self) -> None:
        """There is no target to record, so emitting a call would invent one."""
        calls = self.calls(
            "       PARA-A.\n           EXEC CICS LINK COMMAREA(WS-X) END-EXEC.\n"
        )
        self.assertEqual(calls, [])

    def test_optional_commarea_and_length_are_absent_not_invented(self) -> None:
        calls = self.calls(
            "       PARA-A.\n           EXEC CICS LINK PROGRAM('PDBSUB') END-EXEC.\n"
        )
        self.assertIsNone(calls[0]["commarea"])
        self.assertIsNone(calls[0]["length"])
        self.assertEqual(calls[0]["parameters"], [])

    def test_call_using_lists_its_arguments(self) -> None:
        calls = self.calls("       PARA-A.\n           CALL 'SUBPGM' USING ARG-ONE ARG-TWO.\n")
        self.assertEqual(calls[0]["call_type"], "CALL")
        self.assertEqual(calls[0]["target"], "SUBPGM")
        self.assertEqual(calls[0]["parameters"], ["ARG-ONE", "ARG-TWO"])

    def test_passing_mode_keywords_are_not_arguments(self) -> None:
        calls = self.calls(
            "       PARA-A.\n           CALL 'SUBPGM' USING BY REFERENCE ARG-ONE BY CONTENT ARG-TWO.\n"
        )
        self.assertEqual(calls[0]["parameters"], ["ARG-ONE", "ARG-TWO"])

    def test_quoted_and_unquoted_targets_are_normalised(self) -> None:
        for literal, expected in (("'SUBPGM'", "SUBPGM"), ('"SUBPGM"', "SUBPGM"), ("SUBPGM", "SUBPGM")):
            with self.subTest(literal=literal):
                calls = self.calls(f"       PARA-A.\n           CALL {literal} USING ARG-ONE.\n")
                self.assertEqual(calls[0]["target"], expected)

    def test_trailing_period_is_not_part_of_the_last_argument(self) -> None:
        calls = self.calls("       PARA-A.\n           CALL 'SUBPGM' USING ARG-ONE.\n")
        self.assertEqual(calls[0]["parameters"], ["ARG-ONE"])

    def test_call_records_carry_the_statement_location(self) -> None:
        calls = self.calls("       PARA-A.\n           CALL 'SUBPGM' USING ARG-ONE.\n")
        self.assertEqual(calls[0]["paragraph"], "PARA-A")
        self.assertEqual(calls[0]["line_start"], 2)


class FieldGroupTest(unittest.TestCase):
    def test_a_group_needs_more_than_one_field(self) -> None:
        groups = builder.field_group_prefixes(
            {"IFACE-CODE": {}, "IFACE-NAME": {}, "LONE-FIELD": {}}
        )
        self.assertIn("IFACE", groups)
        self.assertNotIn("LONE", groups)

    def test_groups_are_longest_first(self) -> None:
        groups = builder.field_group_prefixes(
            {"AB-ONE": {}, "AB-TWO": {}, "ABCDEF-ONE": {}, "ABCDEF-TWO": {}}
        )
        self.assertEqual(groups, ["ABCDEF", "AB"])

    def test_undivided_names_form_no_group(self) -> None:
        self.assertEqual(builder.field_group_prefixes({"FLAG": {}, "COUNT": {}}), [])


class ParameterPrefixTest(unittest.TestCase):
    """A call argument names a field group but rarely equals it: the area is
    conventionally named for the interface with a local prefix or suffix."""

    def test_prefixed_area_resolves_to_its_group(self) -> None:
        self.assertEqual(builder.parameter_prefix("WIFACE", ["IFACE"]), "IFACE")

    def test_suffixed_area_resolves_to_its_group(self) -> None:
        self.assertEqual(builder.parameter_prefix("IFACE-AREA", ["IFACE"]), "IFACE")

    def test_longest_matching_group_wins(self) -> None:
        self.assertEqual(builder.parameter_prefix("WABCDEF", ["ABCDEF", "AB"]), "ABCDEF")

    def test_argument_matching_no_group_is_its_own_prefix(self) -> None:
        self.assertEqual(builder.parameter_prefix("some-area", ["IFACE"]), "SOME-AREA")

    def test_argument_equal_to_a_group_is_left_alone(self) -> None:
        self.assertEqual(builder.parameter_prefix("IFACE", ["IFACE"]), "IFACE")

    def test_lookup_is_case_insensitive(self) -> None:
        self.assertEqual(builder.parameter_prefix("wiface", ["IFACE"]), "IFACE")


class VariableSummaryTest(unittest.TestCase):
    @staticmethod
    def variables(**spec: tuple[list[int], list[int]]) -> dict[str, dict[str, Any]]:
        return {
            name.replace("__", "-"): {
                "evidence": {
                    "write_sites": [{"line_start": n} for n in writes],
                    "read_sites": [{"line_start": n} for n in reads],
                }
            }
            for name, (writes, reads) in spec.items()
        }

    def test_only_the_commarea_group_is_summarised(self) -> None:
        """Matching must respect the name boundary: a variable that merely
        starts with the same characters belongs to a different group."""
        variables = self.variables(
            PXCSEMAF=([1], []),
            PXCSEMAF__REQ=([1], []),
            PXCSEMAFX=([1], []),
            OTHER__FIELD=([1], []),
        )
        summary = builder.variable_summary("PXCSEMAF", variables, 10)
        self.assertEqual([item["variable"] for item in summary], ["PXCSEMAF", "PXCSEMAF-REQ"])

    def test_writes_are_limited_to_those_before_the_call(self) -> None:
        variables = self.variables(WS__A=([5, 50], []))
        summary = builder.variable_summary("WS-A", variables, 10)
        self.assertEqual([s["line_start"] for s in summary[0]["writes_before_call"]], [5])

    def test_reads_are_limited_to_those_after_the_call(self) -> None:
        variables = self.variables(WS__A=([], [5, 50]))
        summary = builder.variable_summary("WS-A", variables, 10)
        self.assertEqual([s["line_start"] for s in summary[0]["reads_after_call"]], [50])

    def test_a_site_on_the_call_line_counts_for_both_sides(self) -> None:
        variables = self.variables(WS__A=([10], [10]))
        summary = builder.variable_summary("WS-A", variables, 10)
        self.assertTrue(summary[0]["writes_before_call"])
        self.assertTrue(summary[0]["reads_after_call"])

    def test_variables_with_no_sites_in_range_are_omitted(self) -> None:
        variables = self.variables(WS__A=([50], [5]))
        self.assertEqual(builder.variable_summary("WS-A", variables, 10), [])

    def test_site_lists_are_capped(self) -> None:
        variables = self.variables(WS__A=(list(range(1, 9)), list(range(20, 28))))
        summary = builder.variable_summary("WS-A", variables, 10)
        self.assertEqual(len(summary[0]["writes_before_call"]), 5)
        self.assertEqual(len(summary[0]["reads_after_call"]), 5)

    def test_the_writes_kept_are_the_ones_nearest_the_call(self) -> None:
        variables = self.variables(WS__A=(list(range(1, 9)), []))
        summary = builder.variable_summary("WS-A", variables, 10)
        self.assertEqual(
            [s["line_start"] for s in summary[0]["writes_before_call"]], [4, 5, 6, 7, 8]
        )

    def test_summary_is_ordered_by_variable_name(self) -> None:
        variables = self.variables(WS__B=([1], []), WS__A=([1], []))
        summary = builder.variable_summary("WS", variables, 10)
        self.assertEqual([item["variable"] for item in summary], ["WS-A", "WS-B"])


if __name__ == "__main__":
    unittest.main()
