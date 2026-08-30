from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


def _load(name: str, relative: str):
    path = Path(__file__).parents[1] / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_load("cobol_conditions", "scripts/pipeline/cobol_conditions.py")
ENRICH = _load("enrich_graph", "scripts/pipeline/enrich_graph.py")


def body(*lines: str) -> list[str]:
    """Paragraph body lines as parse_procedure_paragraphs would supply them."""
    return ["           " + line for line in lines]


class GuardExtractionTest(unittest.TestCase):
    def guards(self, *lines: str) -> dict[str, list[str]]:
        raw = ENRICH.extract_paragraph_guards(body(*lines))
        return {target: [g.condition for g in guards] for target, guards in raw.items()}

    def guard_lines(self, *lines: str) -> dict[str, list[int | None]]:
        numbers = list(range(1, len(lines) + 1))
        raw = ENRICH.extract_paragraph_guards(body(*lines), numbers)
        return {target: [g.line for g in guards] for target, guards in raw.items()}

    def test_inline_guarded_jump(self) -> None:
        self.assertEqual(
            self.guards("IF WS-FLAG = 1 THEN GO TO TARGET-A."),
            {"TARGET-A": ["WS-FLAG = 1"]},
        )

    def test_guard_on_the_following_line(self) -> None:
        self.assertEqual(
            self.guards("IF WS-FLAG = 1 THEN", "GO TO TARGET-A."),
            {"TARGET-A": ["WS-FLAG = 1"]},
        )

    def test_guarded_perform_is_a_conditional_edge(self) -> None:
        """A guarded PERFORM is conditional in exactly the way a guarded GO TO
        is; restricting conditions to jumps left these edges unguarded."""
        self.assertEqual(
            self.guards("IF WS-FLAG = 1 THEN", "PERFORM DO-WORK."),
            {"DO-WORK": ["WS-FLAG = 1"]},
        )

    def test_condition_continuing_because_the_line_ends_on_a_connective(self) -> None:
        self.assertEqual(
            self.guards(
                "IF WS-A NOT = '__' AND",
                "   WS-B NOT = SPACES",
                "   THEN GO TO TARGET-A.",
            ),
            {"TARGET-A": ["WS-A NOT = '__' AND WS-B NOT = SPACES"]},
        )

    def test_condition_continuing_because_the_next_line_begins_with_one(self) -> None:
        """The connective may lead the continuation line instead of trailing
        the first. Only the trailing form used to be recognised, which dropped
        every conjunct after the first."""
        self.assertEqual(
            self.guards(
                "IF (WS-A = 'I' OR 'A')",
                "AND WS-B = 'IP'",
                "THEN GO TO TARGET-A.",
            ),
            {"TARGET-A": ["(WS-A = 'I' OR WS-A = 'A') AND WS-B = 'IP'"]},
        )

    def test_nested_conditions_are_conjoined(self) -> None:
        self.assertEqual(
            self.guards(
                "IF WS-A = 1",
                "THEN",
                "   IF WS-B = 2",
                "   THEN",
                "      GO TO TARGET-A",
                "   END-IF",
                "END-IF",
            ),
            {"TARGET-A": ["WS-A = 1 AND WS-B = 2"]},
        )

    def test_independent_guards_to_one_target_stay_separate(self) -> None:
        """Two IF statements each ending in a period are alternative paths, not
        one conjunction. Leaving the first guard on the stack reported them as
        a single condition that no run of the program can satisfy."""
        self.assertEqual(
            self.guards(
                "IF WS-A GREATER 1 THEN",
                "    GO TO TARGET-A.",
                "IF WS-B GREATER 2 THEN",
                "    GO TO TARGET-A.",
            ),
            {"TARGET-A": ["WS-A GREATER 1", "WS-B GREATER 2"]},
        )

    def test_repeated_identical_guards_are_recorded_once(self) -> None:
        self.assertEqual(
            self.guards(
                "IF WS-A = 1 THEN",
                "    GO TO TARGET-A.",
                "IF WS-A = 1 THEN",
                "    GO TO TARGET-A.",
            ),
            {"TARGET-A": ["WS-A = 1"]},
        )

    def test_unguarded_jump_after_a_ladder_is_the_fallback(self) -> None:
        self.assertEqual(
            self.guards(
                "IF WS-A = 1 THEN GO TO TARGET-A.",
                "IF WS-A = 2 THEN GO TO TARGET-B.",
                "GO TO TARGET-C.",
            )["TARGET-C"],
            ["NOT (WS-A = 1 OR WS-A = 2)"],
        )

    def test_single_guard_fallback_is_negated_in_place(self) -> None:
        self.assertEqual(
            self.guards(
                "IF WS-A NOT GREATER 1 THEN",
                "    GO TO TARGET-A.",
                "GO TO TARGET-B.",
            )["TARGET-B"],
            ["WS-A GREATER 1"],
        )

    def test_else_negates_the_enclosing_guard(self) -> None:
        self.assertEqual(
            self.guards(
                "IF WS-A = 1",
                "THEN",
                "   GO TO TARGET-A",
                "ELSE",
                "   GO TO TARGET-B",
                "END-IF",
            ),
            {"TARGET-A": ["WS-A = 1"], "TARGET-B": ["WS-A NOT = 1"]},
        )

    def test_comment_lines_are_not_scanned(self) -> None:
        self.assertEqual(
            self.guards(
                "IF WS-A = 1 THEN",
                "    GO TO TARGET-A.",
            )
            | {},
            {"TARGET-A": ["WS-A = 1"]},
        )

    def test_unguarded_jump_with_no_ladder_has_no_condition(self) -> None:
        self.assertEqual(self.guards("GO TO TARGET-A."), {})

    def test_perform_keywords_are_not_targets(self) -> None:
        guards = self.guards("IF WS-A = 1 THEN", "PERFORM UNTIL WS-B = 2.")
        self.assertNotIn("UNTIL", guards)

    def test_each_guard_records_the_line_of_its_own_branch(self) -> None:
        """Distinct guarded paths sit at distinct places in the source. Cloning
        one edge's line onto all of them cites the wrong statement."""
        self.assertEqual(
            self.guard_lines(
                "IF WS-A GREATER 1 THEN",
                "    GO TO TARGET-A.",
                "IF WS-B GREATER 2 THEN",
                "    GO TO TARGET-A.",
            ),
            {"TARGET-A": [2, 4]},
        )

    def test_line_numbers_survive_comment_lines(self) -> None:
        numbers = [1, 2, 3, 4]
        raw = ENRICH.extract_paragraph_guards(
            ["      * a comment", "           IF WS-A = 1 THEN", "           GO TO TARGET-A.", "      * another"],
            numbers,
        )
        self.assertEqual([g.line for g in raw["TARGET-A"]], [3])

    def test_no_condition_contains_unbalanced_parentheses(self) -> None:
        for conditions in self.guards(
            "IF (WS-A = 'I' OR 'A' OR 'C')",
            "AND WS-B = 'IP'",
            "THEN",
            "   IF WS-C = 1",
            "   THEN",
            "      GO TO TARGET-A",
            "   END-IF",
            "END-IF",
        ).values():
            for condition in conditions:
                with self.subTest(condition=condition):
                    self.assertEqual(condition.count("("), condition.count(")"))


if __name__ == "__main__":
    unittest.main()
