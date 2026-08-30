from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


def _load(name: str, relative: str):
    path = Path(__file__).parents[1] / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ENRICH = _load("enrich_graph", "scripts/pipeline/enrich_graph.py")
DATAFLOW = _load("extract_dataflow", "scripts/pipeline/extract_dataflow.py")


# Area A starts at column 8; a label there is a paragraph, the same text in
# Area B is a statement. Build fixtures with real column positions.
def line(text: str, *, area_a: bool = False) -> str:
    return " " * (7 if area_a else 11) + text


PROGRAM = "\n".join(
    [
        line("IDENTIFICATION DIVISION.", area_a=True),
        line("PROGRAM-ID. TESTPROG.", area_a=True),
        line("PROCEDURE DIVISION.", area_a=True),
        line("MOVE 1 TO WS-COUNT."),
        line("PERFORM DO-WORK."),
        line("DO-WORK.", area_a=True),
        line("IF WS-COUNT = 1"),
        line("THEN MOVE 'A' TO WS-CODE"),
        line("END-IF."),
        line("ORPHAN-PARA.", area_a=True),
        line("EXIT."),
        line("DO-WORK-EXIT.", area_a=True),
        line("EXIT."),
    ]
)


class ParagraphParsingTest(unittest.TestCase):
    def paragraphs(self):
        _paras, order, _lines = ENRICH.parse_procedure_paragraphs(PROGRAM)
        return order

    def test_statement_terminators_are_not_paragraphs(self) -> None:
        """EXIT. and END-IF. sit in Area B and are statements, not labels."""
        order = self.paragraphs()
        self.assertNotIn("EXIT", order)
        self.assertNotIn("END-IF", order)

    def test_real_paragraphs_are_found(self) -> None:
        order = self.paragraphs()
        for name in ("DO-WORK", "ORPHAN-PARA", "DO-WORK-EXIT"):
            self.assertIn(name, order)

    def test_implicit_leading_paragraph_is_named_after_the_program(self) -> None:
        # Every component must agree on this name or citations cannot be joined.
        self.assertEqual(self.paragraphs()[0], "TESTPROG")

    def test_statements_after_a_terminator_keep_their_paragraph(self) -> None:
        paras, _order, _lines = ENRICH.parse_procedure_paragraphs(PROGRAM)
        self.assertNotIn("EXIT", paras)


class IsolatedNodeTest(unittest.TestCase):
    """A paragraph with no edges must still be a node.

    The graph arrives as a DOT edge list, so nodes are edge endpoints; without
    an explicit union, an unreferenced or EXIT-only paragraph disappears and the
    graph reports fewer paragraphs than the program has.
    """

    def test_declared_paragraphs_become_nodes(self) -> None:
        graph = {
            "graph": {"name": "TESTPROG"},
            "nodes": ["TESTPROG", "DO-WORK"],
            "edges": [{"from": "TESTPROG", "to": "DO-WORK"}],
        }
        enriched = ENRICH.enrich_graph(graph, PROGRAM)
        for name in ("ORPHAN-PARA", "DO-WORK-EXIT"):
            self.assertIn(name, enriched["nodes"])

    def test_isolated_nodes_are_recorded(self) -> None:
        graph = {
            "graph": {"name": "TESTPROG"},
            "nodes": ["TESTPROG", "DO-WORK"],
            "edges": [{"from": "TESTPROG", "to": "DO-WORK"}],
        }
        enriched = ENRICH.enrich_graph(graph, PROGRAM)
        isolated = enriched["meta"]["isolated_nodes"]
        self.assertIn("ORPHAN-PARA", isolated)
        self.assertNotIn("DO-WORK", isolated)


class DataflowParagraphNamingTest(unittest.TestCase):
    def test_implicit_paragraph_uses_supplied_program_name(self) -> None:
        statements = [(1, "MOVE 1 TO WS-COUNT."), (2, "DO-WORK."), (3, "MOVE 2 TO WS-B.")]
        paras = DATAFLOW.split_into_paragraphs(statements, top_name="TESTPROG")
        self.assertIn("TESTPROG", paras)
        self.assertNotIn("TOP", paras)

    def test_program_id_is_read_from_source(self) -> None:
        statements = [(1, "IDENTIFICATION DIVISION."), (2, "PROGRAM-ID. TESTPROG.")]
        self.assertEqual(DATAFLOW.get_program_id(statements), "TESTPROG")


if __name__ == "__main__":
    unittest.main()
