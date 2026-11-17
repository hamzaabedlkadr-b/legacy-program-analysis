"""Application-independent regressions for inventory and summary evidence."""
import importlib.util
import sys
from pathlib import Path
import unittest


def load(name):
    path = Path(__file__).parents[1] / 'scripts' / 'pipeline' / (name + '.py')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


dataflow = load('extract_dataflow')
mapa = load('script3')


class SummaryAndInventoryTest(unittest.TestCase):
    def test_io_clause_keywords_are_not_variables(self):
        for statement in (
            "READ INPUT-FILE AT END MOVE '1' TO EOF-FLAG END-READ",
            'WRITE OUTPUT-RECORD INVALID KEY MOVE 1 TO ERROR-FLAG END-WRITE',
            'ADD WS-NUM TO WS-TOTAL ON SIZE ERROR CONTINUE END-ADD',
        ):
            names = dataflow.extract_identifiers(statement)
            self.assertFalse(set(names) & {'AT', 'END', 'INVALID', 'KEY', 'SIZE', 'ERROR'})

    def test_keyword_substrings_remain_real_identifiers(self):
        names = dataflow.extract_identifiers('MOVE AT-END-COUNT TO INVALID-KEY-FLAG')
        self.assertEqual(names, ['AT-END-COUNT', 'INVALID-KEY-FLAG'])

    def test_unknown_environment_is_not_labelled_cics_or_batch(self):
        facts = mapa.ProgramFacts('UNSEEN01')
        summary = next(doc for doc in mapa.build_rag_docs(facts) if doc['type'] == 'program.summary')
        self.assertNotIn('COBOL CICS', summary['embedding_text'])
        self.assertNotIn('CICS program', str(summary['content']))
        self.assertEqual(summary['meta']['execution_environment'], 'unknown')

    def test_positive_cics_usage_is_recorded_with_provenance(self):
        for kind in ('CICSLINKBYLITERAL', 'CICSXCTLBYIDENTIFIER'):
            facts = mapa.ProgramFacts('UNSEEN02')
            facts.calls[kind].append('SERVICE')
            summary = next(doc for doc in mapa.build_rag_docs(facts) if doc['type'] == 'program.summary')
            self.assertEqual(summary['meta']['execution_environment'], 'cics_usage_recorded')
            self.assertEqual(summary['meta']['classification_basis'], 'positive MAPA CICS records')
