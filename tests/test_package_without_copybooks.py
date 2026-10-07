from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.pipeline.package_program_inputs import package_program


class PackageWithoutCopybooksTests(unittest.TestCase):
    def test_program_without_copy_statements_has_empty_copybook_directory(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "ABENDUSR.CBL"
            source.write_text("IDENTIFICATION DIVISION.\nPROGRAM-ID. ABENDUSR.\nPROCEDURE DIVISION.\nSTOP RUN.\n")
            copybooks = root / "copybooks"
            copybooks.mkdir()
            args = Namespace(
                out_dir=root / "packages", cpy_dir=copybooks,
                jcl_dir=None, recursive=False, copy_mode="referenced", dry_run=False,
            )
            manifest = package_program(source, args, {}, {}, {})
            self.assertEqual(manifest.files["copybooks"], [])
            self.assertTrue((root / "packages" / "ABENDUSR" / "copybooks").is_dir())
