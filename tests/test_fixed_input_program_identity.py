import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.pipeline import run_fixed_input


class FixedInputProgramIdentityTests(unittest.TestCase):
    def _run(self, source_stem: str, program_id: str, *, use_program_id: bool = False) -> tuple[list[str], str]:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            program_dir = root / "input" / source_stem
            program_dir.mkdir(parents=True)
            (program_dir / "copybooks").mkdir()
            (program_dir / f"{source_stem}.CBL").write_text(
                f"       PROGRAM-ID. {program_id}.\n", encoding="utf-8"
            )
            (program_dir / f"{source_stem}_result.txt").write_text("", encoding="utf-8")
            (program_dir / f"{source_stem}_controlflow.json").write_text("{}", encoding="utf-8")
            output = root / "output"
            argv = [
                "run_fixed_input.py", "--program", source_stem,
                "--input-root", str(root / "input"),
                "--output-root", str(output), "--mode", "my", "--dry-run",
            ]
            if use_program_id:
                argv.append("--use-program-id")
            with patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(run_fixed_input.main(), 0)
            summary = json.loads((output / "fixed_input_run_summary.json").read_text())
            command = next(
                stage["command"] for stage in summary["stages"]
                if stage["stage"] == "build final_scripts output and RAG JSONL"
            )
            return command, summary["programs"][0]["program"]

    def test_mismatched_filename_uses_configured_name_by_default(self):
        command, program = self._run("PD1FAM", "PD1FAM2")
        self.assertNotIn("--use-program-id", command)
        self.assertEqual("PD1FAM", program)

    def test_matching_filename_keeps_existing_factory_default(self):
        command, program = self._run("PDCBVC", "PDCBVC")
        self.assertNotIn("--use-program-id", command)
        self.assertEqual("PDCBVC", program)

    def test_explicit_program_id_selects_source_identity_end_to_end(self):
        command, program = self._run("PD1FAM", "PD1FAM2", use_program_id=True)
        self.assertIn("--use-program-id", command)
        self.assertEqual("PD1FAM2", program)


if __name__ == "__main__":
    unittest.main()
