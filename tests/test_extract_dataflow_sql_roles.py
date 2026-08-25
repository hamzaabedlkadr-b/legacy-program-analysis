from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "pipeline" / "extract_dataflow.py"
SPEC = importlib.util.spec_from_file_location("extract_dataflow", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SqlAccessRoleTest(unittest.TestCase):
    def test_select_into_host_variable_is_a_write(self) -> None:
        writes, reads, _read_writes, _subscripts = MODULE.detect_statement_accesses(
            "EXEC SQL SELECT SYSDATE INTO :HSQL-DATE FROM DUAL END-EXEC"
        )
        self.assertIn("HSQL-DATE", writes)
        self.assertNotIn("HSQL-DATE", reads)

    def test_whenever_go_to_target_is_not_a_variable(self) -> None:
        statement = "EXEC SQL WHENEVER SQLERROR GO TO ERRORE-SQL END-EXEC"
        self.assertEqual(MODULE.extract_explicit_targets(statement), {"ERRORE-SQL"})
        writes, reads, _read_writes, _subscripts = MODULE.detect_statement_accesses(statement)
        self.assertEqual(writes, set())
        self.assertNotIn("ERRORE-SQL", reads)

    def test_unresolved_sql_flow_target_is_not_seeded(self) -> None:
        source = "\n".join((
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. SAMPLE.",
            "       DATA DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01 HSQL-DATE PIC X(10).",
            "       PROCEDURE DIVISION.",
            "       TOP.",
            "           EXEC SQL WHENEVER SQLERROR GO TO ERRORE-SQL END-EXEC.",
            "           EXEC SQL SELECT SYSDATE INTO :HSQL-DATE FROM DUAL END-EXEC.",
            "           GOBACK.",
        ))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "SAMPLE.CBL"
            path.write_text(source, encoding="utf-8")
            variables = MODULE.improve_index(path, None, None, None)
        by_name = {item["variable"]: item for item in variables}
        self.assertNotIn("ERRORE-SQL", by_name)
        self.assertIn("HSQL-DATE", by_name)
        self.assertEqual(by_name["HSQL-DATE"]["modified_in"], ["TOP"])


if __name__ == "__main__":
    unittest.main()
