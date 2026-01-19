import os
import tempfile
import unittest
from pathlib import Path

from packager.models import PackPlanItem
from packager.core.pack import execute_pack


class TestPack(unittest.TestCase):
    def test_execute_pack_copies_files(self):
        with tempfile.TemporaryDirectory() as tin, tempfile.TemporaryDirectory() as tout:
            tinp = Path(tin)
            toutp = Path(tout)

            # Create dummy source file
            src_dir = tinp / "geo"
            src_dir.mkdir(parents=True, exist_ok=True)
            src_file = src_dir / "CrateA_v001.fbx"
            src_file.write_bytes(b"dummydata")

            dst_file = toutp / "Proj" / "CrateA" / "v001" / "export" / "fbx" / "CrateA_v001.fbx"

            plan = [
                PackPlanItem(
                    src=str(src_file),
                    relpath="geo/CrateA_v001.fbx",
                    dst=str(dst_file),
                    category="export/fbx",
                )
            ]

            summary, issues, hashes = execute_pack(plan, overwrite=False)
            self.assertEqual(summary.copied, 1)
            self.assertTrue(Path(dst_file).exists())
            self.assertEqual(Path(dst_file).read_bytes(), b"dummydata")
            self.assertFalse(any(i.level.upper() == "ERROR" for i in issues))
            self.assertIn(str(src_file), hashes)
            self.assertTrue(len(hashes[str(src_file)]) >= 32)

    def test_execute_pack_skips_existing_when_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tin, tempfile.TemporaryDirectory() as tout:
            tinp = Path(tin)
            toutp = Path(tout)

            src_file = tinp / "A_v001.txt"
            src_file.write_text("one")

            dst_file = toutp / "drop" / "A_v001.txt"
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            dst_file.write_text("existing")

            plan = [
                PackPlanItem(
                    src=str(src_file),
                    relpath="A_v001.txt",
                    dst=str(dst_file),
                    category="docs",
                )
            ]

            summary, issues, hashes = execute_pack(plan, overwrite=False)
            self.assertEqual(summary.copied, 0)
            self.assertEqual(summary.skipped, 1)
            self.assertEqual(dst_file.read_text(), "existing")
            self.assertTrue(any(i.code == "DST_EXISTS_SKIPPED" for i in issues))
            self.assertIn(str(src_file), hashes)
            self.assertTrue(len(hashes[str(src_file)]) >= 32)

if __name__ == "__main__":
    unittest.main()
