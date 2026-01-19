import json
import tempfile
import unittest
from pathlib import Path

from packager.core.manifest import build_manifest_dict, write_manifest_json
from packager.models import ValidationResult, PackPlanItem


class TestManifest(unittest.TestCase):
    def test_manifest_write(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)

            plan = [
                PackPlanItem(
                    src=str(out / "srcA.txt"),
                    relpath="srcA.txt",
                    dst=str(out / "Proj" / "Asset" / "v001" / "docs" / "srcA.txt"),
                    category="docs",
                )
            ]
            # create source so stats work
            (out / "srcA.txt").write_text("hello", encoding="utf-8")

            results = [ValidationResult("INFO", "OK", "All good", None)]

            manifest = build_manifest_dict(
                tool_name="Tool",
                tool_version="0.0",
                profile="VFX",
                input_root="C:/in",
                output_root=str(out),
                project="Proj",
                asset_name="Asset",
                version="v001",
                validation_results=results,
                plan=plan,
                include_file_stats=True,
            )

            path = write_manifest_json(manifest, str(out / "manifest.json"))
            self.assertTrue(Path(path).exists())

            loaded = json.loads(Path(path).read_text(encoding="utf-8"))
            self.assertEqual(loaded["tool"], "Tool")
            self.assertEqual(len(loaded["files"]), 1)
            self.assertIn("size_bytes", loaded["files"][0])

if __name__ == "__main__":
    unittest.main()
