from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "pipeline" / "cobol_conditions.py"
SPEC = importlib.util.spec_from_file_location("cobol_conditions", SCRIPT)
assert SPEC and SPEC.loader
cc = importlib.util.module_from_spec(SPEC)
sys.modules["cobol_conditions"] = cc
SPEC.loader.exec_module(cc)


class ParseAndRenderTest(unittest.TestCase):
    def round_trip(self, text: str) -> str:
        return cc.condition_text(text)

    def test_simple_relation_is_preserved(self) -> None:
        self.assertEqual(self.round_trip("WCTRIG  GREATER      15"), "WCTRIG GREATER 15")

    def test_redundant_parentheses_are_dropped(self) -> None:
        self.assertEqual(self.round_trip("(((TWCOB-FUNZIONE = 'I')))"), "TWCOB-FUNZIONE = 'I'")

    def test_and_binds_tighter_than_or(self) -> None:
        # A OR (B AND C) needs no parentheses; (A OR B) AND C does.
        self.assertEqual(self.round_trip("A1 = 1 OR B1 = 2 AND C1 = 3"), "A1 = 1 OR B1 = 2 AND C1 = 3")
        self.assertEqual(self.round_trip("(A1 = 1 OR B1 = 2) AND C1 = 3"), "(A1 = 1 OR B1 = 2) AND C1 = 3")

    def test_rendering_is_stable_under_reparsing(self) -> None:
        """Rendered output must parse back to the same thing, or conditions
        drift every time one passes through the pipeline."""
        for text in (
            "(A1 = 1 OR B1 = 2) AND C1 = 3",
            "NOT (A1 = 1 OR B1 = 2)",
            "A1 = 1 AND B1 = 2 AND C1 = 3",
        ):
            with self.subTest(text=text):
                once = self.round_trip(text)
                self.assertEqual(self.round_trip(once), once)

    def test_unbalanced_input_does_not_produce_stray_parentheses(self) -> None:
        rendered = self.round_trip("((A1 = 1 OR B1 = 2")
        self.assertEqual(rendered.count("("), rendered.count(")"))
        self.assertNotIn("))", rendered)

    def test_trailing_connective_is_not_treated_as_an_operand(self) -> None:
        self.assertEqual(self.round_trip("A1 = 1 AND"), "A1 = 1")


class AbbreviatedRelationTest(unittest.TestCase):
    """COBOL lets the subject and operator carry over: X = 'A' OR 'B'."""

    def test_subject_and_operator_carry_over(self) -> None:
        self.assertEqual(
            cc.condition_text("TWCOB-FUNZIONE = 'I' OR 'A' OR 'C'"),
            "TWCOB-FUNZIONE = 'I' OR TWCOB-FUNZIONE = 'A' OR TWCOB-FUNZIONE = 'C'",
        )

    def test_explicit_relations_are_left_alone(self) -> None:
        self.assertEqual(
            cc.condition_text("A1 = 'I' OR B1 = 'A'"), "A1 = 'I' OR B1 = 'A'"
        )

    def test_expansion_survives_surrounding_parentheses(self) -> None:
        self.assertEqual(
            cc.condition_text("(TWCOB-FUNZIONE = 'I' OR 'A') AND TWCOB-ID = 'IP'"),
            "(TWCOB-FUNZIONE = 'I' OR TWCOB-FUNZIONE = 'A') AND TWCOB-ID = 'IP'",
        )


class NormalisationTest(unittest.TestCase):
    def test_repeated_operands_collapse(self) -> None:
        expr = cc.disjoin([cc.parse_condition("A1 = 1"), cc.parse_condition("A1 = 1")])
        self.assertEqual(cc.render(expr), "A1 = 1")

    def test_absorption(self) -> None:
        expr = cc.disjoin(
            [cc.parse_condition("A1 = 1"), cc.parse_condition("A1 = 1 AND B1 = 2")]
        )
        self.assertEqual(cc.render(expr), "A1 = 1")

    def test_nested_same_kind_is_flattened(self) -> None:
        inner = cc.conjoin(cc.parse_condition("A1 = 1"), cc.parse_condition("B1 = 2"))
        outer = cc.conjoin(inner, cc.parse_condition("C1 = 3"))
        self.assertEqual(cc.render(outer), "A1 = 1 AND B1 = 2 AND C1 = 3")

    def test_conjoin_ignores_absent_operands(self) -> None:
        self.assertEqual(cc.render(cc.conjoin(None, cc.parse_condition("A1 = 1"))), "A1 = 1")
        self.assertIsNone(cc.conjoin(None, None))


class NegationTest(unittest.TestCase):
    """COBOL negates a relation in place, so a negated guard reads naturally."""

    def test_negating_a_relation_inserts_not_in_place(self) -> None:
        self.assertEqual(cc.render(cc.negate(cc.parse_condition("WCTPAG = 1"))), "WCTPAG NOT = 1")

    def test_negating_an_already_negated_relation_removes_the_not(self) -> None:
        self.assertEqual(
            cc.render(cc.negate(cc.parse_condition("WCTPAG NOT GREATER 1"))), "WCTPAG GREATER 1"
        )

    def test_both_spellings_normalise_to_one_form(self) -> None:
        """"NOT (A = B)" and "A NOT = B" must not compare as different."""
        self.assertEqual(cc.condition_text("NOT (WCTPAG = 1)"), cc.condition_text("WCTPAG NOT = 1"))

    def test_compound_negation_is_kept_as_a_wrapper(self) -> None:
        expr = cc.negate(cc.disjoin([cc.parse_condition("A1 = 1"), cc.parse_condition("B1 = 2")]))
        self.assertEqual(cc.render(expr), "NOT (A1 = 1 OR B1 = 2)")

    def test_double_negation_cancels(self) -> None:
        expr = cc.negate(cc.negate(cc.disjoin([cc.parse_condition("A1 = 1"), cc.parse_condition("B1 = 2")])))
        self.assertEqual(cc.render(expr), "A1 = 1 OR B1 = 2")


if __name__ == "__main__":
    unittest.main()
