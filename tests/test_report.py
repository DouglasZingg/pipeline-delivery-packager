import tempfile
import unittest
from pathlib import Path

from packager.core.reporting import build_report_html, write_report_html
from packager.models import ValidationResult, PackPlanItem


class TestReport(unittest.TestCase):
    def test_report_writes_html(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)

            results = [
                ValidationResult("WARNING", "VERSION_TOKEN_MISSING", "Missing version token", "geo/A.fbx")
            ]
            plan = [
                PackPlanItem(
                    src=str(out / "A.txt"),
                    relpath="A.txt",
                    dst=str(out / "Proj/Asset/v001/docs/A.txt"),
                    category="docs",
                )
            ]
            (out / "A.txt").write_text("hello", encoding="utf-8")

            html_text = build_report_html(
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
                hashes_by_src={str(out / "A.txt"): "abc123"},
                hash_algo="sha1",
            )

            path = write_report_html(html_text, str(out / "report.html"))
            self.assertTrue(Path(path).exists())
            content = Path(path).read_text(encoding="utf-8")
            self.assertIn("<!doctype html>", content.lower())
            self.assertIn("validation", content.lower())
            self.assertIn("packaging plan", content.lower())


if __name__ == "__main__":
    unittest.main()
