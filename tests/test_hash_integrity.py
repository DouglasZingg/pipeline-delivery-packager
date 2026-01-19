import tempfile
import unittest
from pathlib import Path
from unittest import mock

from packager.core.pack import execute_pack
from packager.models import PackPlanItem


class TestHashIntegrity(unittest.TestCase):
    def test_hash_mismatch_detected(self):
        with tempfile.TemporaryDirectory() as tin, tempfile.TemporaryDirectory() as tout:
            tinp = Path(tin)
            toutp = Path(tout)

            src = tinp / "A_v001.bin"
            src.write_bytes(b"AAAAAA")

            dst = toutp / "Proj" / "Asset" / "v001" / "export" / "fbx" / "A_v001.bin"

            plan = [
                PackPlanItem(
                    src=str(src),
                    relpath="A_v001.bin",
                    dst=str(dst),
                    category="export/fbx",
                )
            ]

            # Copy correctly, then corrupt destination to force mismatch
            real_copy2 = __import__("shutil").copy2

            def corrupting_copy2(s, d, *args, **kwargs):
                r = real_copy2(s, d, *args, **kwargs)
                Path(d).write_bytes(b"BBBBBB")  # corrupt
                return r

            with mock.patch("shutil.copy2", side_effect=corrupting_copy2):
                summary, issues, hashes = execute_pack(plan, verify_hash=True, hash_algo="sha1")

            self.assertTrue(any(i.code == "HASH_MISMATCH" for i in issues))
            self.assertGreaterEqual(summary.failed, 1)
            self.assertIn(str(src), hashes)


if __name__ == "__main__":
    unittest.main()
