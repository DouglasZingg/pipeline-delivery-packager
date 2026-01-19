import unittest
import tempfile
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from packager.ui.main_window import MainWindow


class TestMainWindowUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure one QApplication exists
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow()
        self.window.show()
        QTest.qWaitForWindowExposed(self.window)

    def tearDown(self):
        self.window.close()

    def test_scan_updates_results_list(self):
        # Create temp input/output folders
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            inp = Path(input_dir)
            out = Path(output_dir)

            # Create a fake asset drop
            (inp / "geo").mkdir(parents=True, exist_ok=True)
            (inp / "tex").mkdir(parents=True, exist_ok=True)
            (inp / "docs").mkdir(parents=True, exist_ok=True)

            (inp / "geo" / "CrateA_v001.fbx").write_bytes(b"dummy")
            (inp / "tex" / "CrateA_v001_diffuse.png").write_bytes(b"dummy")
            (inp / "docs" / "readme.md").write_text("hello")

            # Fill fields directly (faster than file dialog)
            input_edit = self.window.findChild(type(self.window.input_edit), "input_edit")
            output_edit = self.window.findChild(type(self.window.output_edit), "output_edit")

            input_edit.setText(str(inp))
            output_edit.setText(str(out))

            # Click Scan
            btn_scan = self.window.findChild(type(self.window.btn_scan), "btn_scan")
            QTest.mouseClick(btn_scan, Qt.LeftButton)

            # Assert results list populated
            results = self.window.findChild(type(self.window.results_list), "results_list")
            self.assertGreater(results.count(), 0)

            # Assert log updated
            log_box = self.window.findChild(type(self.window.log_box), "log_box")
            self.assertIn("SCAN", log_box.toPlainText())

    def test_preview_plan_creates_plan_results(self):
        # Only works if your UI has Day 4 preview + stores self._last_plan
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            inp = Path(input_dir)
            out = Path(output_dir)

            (inp / "geo").mkdir(parents=True, exist_ok=True)
            (inp / "geo" / "CrateA_v001.fbx").write_bytes(b"dummy")

            self.window.input_edit.setText(str(inp))
            self.window.output_edit.setText(str(out))

            # Fill Project/Asset/Version
            self.window.project_edit.setText("DemoProj")
            self.window.asset_edit.setText("CrateA")
            self.window.version_edit.setText("v001")

            # Click Preview (NOT Package)
            btn_preview = self.window.findChild(type(self.window.btn_preview), "btn_preview")
            self.assertIsNotNone(btn_preview, "Preview button not found (objectName='btn_preview')")

            QTest.mouseClick(btn_preview, Qt.LeftButton)

            # Let Qt process the click + UI updates
            QTest.qWait(100)

            results = self.window.results_list
            self.assertGreater(results.count(), 0)


if __name__ == "__main__":
    unittest.main()
