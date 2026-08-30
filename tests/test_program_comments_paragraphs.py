from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).parents[1]
    / "artifacts/final/final_scripts/program.comments/build_program_comments.py"
)
SPEC = importlib.util.spec_from_file_location("build_program_comments", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def record(text: str, *, indicator: str = " ", area_a: bool = False) -> str:
    """One fixed-format record: cols 1-6 sequence, col 7 indicator, code from 8."""
    return "      " + indicator + (" " * (0 if area_a else 4)) + text


class ParagraphDetectionTest(unittest.TestCase):
    """A paragraph label is live code in Area A.

    Matching on text alone counts commented-out labels and Area B statement
    terminators, both of which inflate the reported paragraph count against
    what the program actually contains.
    """

    def detect(self, line: str) -> bool:
        code, indicator = MODULE.normalize_line_fixed_format(line)
        return bool(
            MODULE.PARA_RE.match(code.upper())
            and indicator not in ("*", "/")
            and code[:1].strip() != ""
        )

    def test_area_a_label_is_a_paragraph(self) -> None:
        self.assertTrue(self.detect(record("DO-WORK.", area_a=True)))

    def test_commented_out_label_is_not_a_paragraph(self) -> None:
        self.assertFalse(self.detect(record("BROWSE-PDKTELR.", indicator="*", area_a=True)))

    def test_slash_comment_label_is_not_a_paragraph(self) -> None:
        self.assertFalse(self.detect(record("LEGGI-RIMBORSO.", indicator="/", area_a=True)))

    def test_area_b_terminator_is_not_a_paragraph(self) -> None:
        for terminator in ("EXIT.", "END-IF.", "END-EXEC."):
            with self.subTest(terminator=terminator):
                self.assertFalse(self.detect(record(terminator)))

    def test_area_a_exit_paragraph_is_still_a_paragraph(self) -> None:
        # DO-WORK-EXIT. is a real paragraph name, unlike a bare EXIT. statement.
        self.assertTrue(self.detect(record("DO-WORK-EXIT.", area_a=True)))


if __name__ == "__main__":
    unittest.main()
