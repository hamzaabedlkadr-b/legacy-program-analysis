import json
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "artifacts/final/final_scripts/jcl/build_jcl_artifacts.py"
PARSER = runpy.run_path(str(BUILDER))


class JclAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def parse(self, text):
        path = self.folder / "JOB.JCL"
        path.write_text(text)
        return PARSER["parse_jcl"](path)

    def test_spacing_continuation_and_concatenation(self):
        data = self.parse("//JOB1 JOB CLASS=A\n//S EXEC PGM=SORT\n//SORTIN DD DSN=A,\n// DISP=SHR\n// DD DSN=B,DISP=SHR\n//SORTOUT DD DSN=C,DISP=(NEW,CATLG,DELETE)\n")
        self.assertEqual(data["programs"], ["SORT"])
        self.assertEqual(data["execution_steps"][0]["reads"], ["A", "B"])
        self.assertEqual(data["execution_steps"][0]["writes"], ["C"])

    def test_symbols_are_resolved_at_each_statement(self):
        data = self.parse("//J JOB CLASS=A\n// SET TARGET=PDB305,HLQ=TEST\n//A EXEC PGM=&TARGET\n//D DD DSN=&HLQ..DATA,DISP=OLD\n// SET TARGET=PDCBVC\n//B EXEC PGM=&TARGET\n")
        self.assertEqual([s["program"] for s in data["execution_steps"]], ["PDB305", "PDCBVC"])
        self.assertEqual(data["execution_steps"][0]["dds"][0]["dsn"], "TEST.DATA")

    def test_existing_dataset_is_not_assumed_read_only(self):
        data = self.parse("//J JOB CLASS=A\n//S EXEC PGM=PDB305\n//MASTER DD DSN=A,DISP=OLD\n")
        self.assertEqual(data["execution_steps"][0]["dds"][0]["access_type"], "unknown")

    def test_proc_parameters_overrides_and_distinct_invocations(self):
        data = self.parse("//J JOB CLASS=A\n//P PROC TARGET=PDB305\n//S EXEC PGM=&TARGET\n//IN DD DSN=DEFAULT.DATA,DISP=SHR\n// PEND\n//CALL1 EXEC P,TARGET=PDCBVC\n//S.IN DD DSN=ACTUAL.DATA\n//CALL2 EXEC P\n")
        steps = data["execution_steps"]
        self.assertEqual([s["step"] for s in steps], ["CALL1.S", "CALL2.S"])
        self.assertEqual([s["program"] for s in steps], ["PDCBVC", "PDB305"])
        self.assertEqual(steps[0]["dds"][0]["dsn"], "ACTUAL.DATA")
        self.assertEqual(steps[0]["dds"][0]["disp"], "SHR")
        self.assertEqual(steps[1]["dds"][0]["dsn"], "DEFAULT.DATA")

    def test_external_procedure_member(self):
        (self.folder / "P.proc").write_text("//P PROC TARGET=PDB305\n//S EXEC PGM=&TARGET\n// PEND\n")
        data = self.parse("//J JOB CLASS=A\n//A EXEC P,TARGET=PDCBVC\n")
        self.assertEqual(data["programs"], ["PDCBVC"])
        self.assertEqual(data["execution_steps"][0]["step"], "A.S")

    def test_dd_dummy_override_removes_dataset(self):
        data = self.parse("//J JOB CLASS=A\n//P PROC\n//S EXEC PGM=PDB305\n//D DD DSN=A,DISP=SHR\n// PEND\n//A EXEC P\n//S.D DD DUMMY\n")
        self.assertFalse(data["execution_steps"][0]["dds"][0].get("dsn"))

    def test_shared_library_does_not_invent_program_job_linkage(self):
        scan = runpy.run_path(str(ROOT / "scripts/pipeline/build_global_rag_maps.py"))["scan_jcl_artifacts"]
        job_dir = self.folder / "_global/jcl/J"
        job_dir.mkdir(parents=True)
        (job_dir / "jcl.summary.json").write_text(json.dumps({"job": "J", "source": "JOB.JCL", "programs": ["PDB305"]}))
        _, summary = scan(self.folder, {"PDCBVC": {"files": {"jcl": ["JOB.JCL", "LIB.proc"]}}})
        self.assertEqual(summary["program_to_jobs"], {"PDB305": ["J"]})

    def test_nested_conditions_and_cond_semantics(self):
        data = self.parse("//J JOB CLASS=A\n// IF (A.RC = 0) THEN\n// IF (B.RC = 0) THEN\n//S EXEC PGM=PDB305,COND=(4,LT)\n// ELSE\n//T EXEC PGM=PDCBVC\n// ENDIF\n// ENDIF\n")
        first, second = data["execution_steps"]
        self.assertEqual(len(first["conditions"]), 3)
        self.assertEqual(first["conditions"][-1]["kind"], "EXEC_COND")
        self.assertEqual(second["conditions"][-1]["branch"], "else")
        self.assertEqual(data["flow"]["execution_steps"][1]["conditions"], second["conditions"])

    def test_instream_data_is_not_parsed_as_job_statements(self):
        data = self.parse("//J JOB CLASS=A\n//A EXEC PGM=PDB305\n//SYSIN DD DATA,DLM='@@'\n//FAKE EXEC PGM=WRONG\n@@\n//B EXEC PGM=PDCBVC\n")
        self.assertEqual(data["programs"], ["PDB305", "PDCBVC"])

    def test_unresolved_and_unsupported_are_visible(self):
        data = self.parse("//J JOB CLASS=A\n// INCLUDE MEMBER=ABSENT\n//A EXEC PGM=&UNKNOWN\n//B EXEC MISSING\n//BAD INVALID FOO\n")
        warnings = " ".join(data["warnings"])
        for phrase in ("INCLUDE", "unresolved symbols", "Unresolved procedure", "unsupported or malformed"):
            self.assertIn(phrase, warnings)

    def test_generated_artifacts_contain_resolved_steps_and_conditions(self):
        self.parse("//J JOB CLASS=A\n//P PROC TARGET=PDB305\n//S EXEC PGM=&TARGET\n//D DD DSN=A,DISP=OLD\n// PEND\n// IF (FIRST.RC = 0) THEN\n//A EXEC P\n// ENDIF\n")
        output = self.folder / "artifacts/jcl/J"
        subprocess.run([sys.executable, str(BUILDER), "--jcl", str(self.folder / "JOB.JCL"), "--output-dir", str(output)], check=True, capture_output=True)
        step = json.loads((output / "jcl.steps.A_S.json").read_text())
        self.assertEqual(step["program"], "PDB305")
        self.assertEqual(step["conditions"][0]["branch"], "then")
        self.assertEqual(step["dds"][0]["access_type"], "unknown")
        rag_module = ROOT.parent / "cobol-rag-pipeline/src/cobol_rag/final_scripts_artifacts.py"
        if rag_module.exists():
            build = runpy.run_path(str(rag_module))["build_jcl_file_io_artifact"]
            artifact = build(self.folder / "artifacts", "PDB305")["content"]
            self.assertEqual(artifact["matching_steps_count"], 1)
            self.assertTrue(artifact["matching_steps"][0]["conditions"])
            self.assertEqual(artifact["unknowns"][0]["dsn"], "A")
            self.assertEqual(artifact["reads"], [])


if __name__ == "__main__":
    unittest.main()
