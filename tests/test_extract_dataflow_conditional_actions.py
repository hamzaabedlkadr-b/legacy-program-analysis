from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "pipeline" / "extract_dataflow.py"
SPEC = importlib.util.spec_from_file_location("extract_dataflow", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ConditionalActionRoleTest(unittest.TestCase):
    """A continuation line may begin with a bare connective when the controlling
    IF/EVALUATE sits on an earlier physical line. The receiving field of the
    embedded action is still a write, not a read."""

    def assert_roles(self, statement, *, writes=(), reads=None):
        got_writes, got_reads, _rw, _subs = MODULE.detect_statement_accesses(statement)
        self.assertEqual(sorted(got_writes), sorted(writes), f"writes for {statement!r}")
        if reads is not None:
            self.assertEqual(sorted(got_reads), sorted(reads), f"reads for {statement!r}")

    def test_then_prefixed_move_is_a_write(self) -> None:
        self.assert_roles("THEN MOVE 'LE10' TO WABEND-CODE", writes=["WABEND-CODE"], reads=[])

    def test_else_prefixed_move_is_a_write(self) -> None:
        self.assert_roles("ELSE MOVE 'X' TO WABEND-CODE", writes=["WABEND-CODE"], reads=[])

    def test_then_prefixed_perform_target_is_not_a_variable(self) -> None:
        # Paragraph names must not leak into the variable inventory as reads.
        self.assert_roles("THEN PERFORM ABEND00", writes=[], reads=[])

    def test_inline_condition_splits_into_condition_and_action(self) -> None:
        self.assert_roles(
            "IF WS-FLAG = 1 THEN MOVE 'L' TO WABEND-CODE",
            writes=["WABEND-CODE"],
            reads=["WS-FLAG"],
        )

    def test_inline_condition_without_then_keyword(self) -> None:
        self.assert_roles("WHEN 1 MOVE 'X' TO WABEND-CODE", writes=["WABEND-CODE"], reads=[])

    def test_stacked_connectives(self) -> None:
        self.assert_roles(
            "ELSE IF WS-YY = 2 THEN MOVE 'X' TO WABEND-CODE",
            writes=["WABEND-CODE"],
            reads=["WS-YY"],
        )

    def test_verb_inside_hyphenated_identifier_is_not_a_split_point(self) -> None:
        # \b is not a safe COBOL boundary: r"\bMOVE\b" matches inside WS-MOVE-FLAG.
        self.assert_roles(
            "IF WS-MOVE-FLAG = 1 THEN MOVE 'A' TO WT-OUT",
            writes=["WT-OUT"],
            reads=["WS-MOVE-FLAG"],
        )

    def test_condition_without_embedded_action_keeps_default_reads(self) -> None:
        self.assert_roles(
            "IF WS-AA = WS-BB AND WS-CC = WS-DD",
            writes=[],
            reads=["WS-AA", "WS-BB", "WS-CC", "WS-DD"],
        )

    def test_then_prefixed_cics_keeps_operand_roles(self) -> None:
        self.assert_roles(
            "THEN EXEC CICS SEND MAP('M') FROM(WS-AREA) END-EXEC",
            writes=[],
            reads=["WS-AREA"],
        )

    def test_plain_move_is_unchanged(self) -> None:
        self.assert_roles("MOVE 'BR00' TO WABEND-CODE", writes=["WABEND-CODE"], reads=[])


if __name__ == "__main__":
    unittest.main()
