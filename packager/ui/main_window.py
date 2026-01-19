import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QSplitter,
    QMessageBox,
)
from packager.core.scanner import scan_folder
from packager.core.profiles import get_profile
from packager.core.validator import validate_delivery


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline Delivery Packager (v0.1)")
        self.setMinimumSize(980, 620)

        # --- Root widget
        root = QWidget()
        self.setCentralWidget(root)

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # -------------------------
        # Top: Input / Output rows
        # -------------------------
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Select input folder (work area)...")

        btn_input = QPushButton("Browse...")
        btn_input.clicked.connect(self.pick_input_folder)

        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("Input:"))
        input_row.addWidget(self.input_edit, 1)
        input_row.addWidget(btn_input)

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Select output folder (delivery target)...")

        btn_output = QPushButton("Browse...")
        btn_output.clicked.connect(self.pick_output_folder)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("Output:"))
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(btn_output)

        main_layout.addLayout(input_row)
        main_layout.addLayout(output_row)

        # -------------------------
        # Mid: Profile + buttons
        # -------------------------
        mid_row = QHBoxLayout()

        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["Game", "VFX", "Mobile"])
        self.profile_combo.setCurrentText("VFX")

        mid_row.addWidget(QLabel("Profile:"))
        mid_row.addWidget(self.profile_combo)

        mid_row.addStretch(1)

        self.btn_scan = QPushButton("Scan")
        self.btn_scan.clicked.connect(self.on_scan_clicked)

        self.btn_package = QPushButton("Package")
        self.btn_package.setEnabled(False)

        self.btn_export = QPushButton("Export Report")
        self.btn_export.setEnabled(False)

        mid_row.addWidget(self.btn_scan)
        mid_row.addWidget(self.btn_package)
        mid_row.addWidget(self.btn_export)

        main_layout.addLayout(mid_row)

        # -------------------------
        # Bottom: Results + Logs
        # -------------------------
        splitter = QSplitter(Qt.Horizontal)

        # Results list (left)
        results_panel = QWidget()
        results_layout = QVBoxLayout(results_panel)
        results_layout.setContentsMargins(0, 0, 0, 0)

        results_layout.addWidget(QLabel("Results"))
        self.results_list = QListWidget()
        results_layout.addWidget(self.results_list, 1)

        # Log panel (right)
        logs_panel = QWidget()
        logs_layout = QVBoxLayout(logs_panel)
        logs_layout.setContentsMargins(0, 0, 0, 0)

        logs_layout.addWidget(QLabel("Log"))
        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Logs will appear here...")
        logs_layout.addWidget(self.log_box, 1)

        splitter.addWidget(results_panel)
        splitter.addWidget(logs_panel)
        splitter.setSizes([560, 420])

        main_layout.addWidget(splitter, 1)

        # Seed with a friendly note
        self.log("Ready. Choose folders and click Scan.")

    # -------------------------
    # UI Helpers
    # -------------------------
    def log(self, msg: str):
        self.log_box.appendPlainText(msg)

    def add_result(self, level: str, message: str):
        """
        Adds a result item with basic severity coloring.
        """
        text = f"[{level}] {message}"
        item = QListWidgetItem(text)

        lvl = level.upper().strip()
        if lvl == "ERROR":
            item.setForeground(Qt.red)
        elif lvl == "WARNING":
            item.setForeground(Qt.darkYellow)
        else:
            item.setForeground(Qt.darkGreen)

        self.results_list.addItem(item)


    def pick_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder:
            self.input_edit.setText(os.path.normpath(folder))
            self.log(f"Input folder set: {folder}")

    def pick_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_edit.setText(os.path.normpath(folder))
            self.log(f"Output folder set: {folder}")

    # -------------------------
    # Buttons
    # -------------------------
    def on_scan_clicked(self):
        self.results_list.clear()

        input_path = self.input_edit.text().strip()
        output_path = self.output_edit.text().strip()
        profile_name = self.profile_combo.currentText()

        if not input_path or not os.path.isdir(input_path):
            QMessageBox.warning(self, "Missing Input", "Please choose a valid input folder.")
            return

        if not output_path or not os.path.isdir(output_path):
            QMessageBox.warning(self, "Missing Output", "Please choose a valid output folder.")
            return

        self.log("---- SCAN START ----")
        self.log(f"Profile: {profile_name}")
        self.log(f"Input:   {input_path}")
        self.log(f"Output:  {output_path}")

        ignore_dirs = {".git", "__pycache__", ".venv", "node_modules"}
        try:
            files, summary = scan_folder(
                input_path,
                ignore_dirs=ignore_dirs,
                ignore_hidden=True,
                follow_symlinks=False,
            )
        except Exception as e:
            self.add_result("ERROR", f"Scan failed: {e}")
            self.log(f"ERROR: {e}")
            return

        # Scan header
        mb = summary.total_bytes / (1024 * 1024) if summary.total_bytes else 0.0
        self.add_result("INFO", f"Scan OK: {summary.total_files} files in {summary.total_dirs} folders ({mb:.2f} MB)")
        self.add_result("INFO", f"Unique extensions: {len(summary.extensions)}")

        # Run validation (Day 3)
        profile = get_profile(profile_name)
        validation_results = validate_delivery(
            input_root=input_path,
            files=files,
            summary=summary,
            profile=profile,
        )

        # Count levels
        counts = {"ERROR": 0, "WARNING": 0, "INFO": 0}
        for r in validation_results:
            lvl = (r.level or "INFO").upper()
            if lvl not in counts:
                counts[lvl] = 0
            counts[lvl] += 1

        self.add_result("INFO", f"Validation: {counts.get('ERROR', 0)} error(s), {counts.get('WARNING', 0)} warning(s)")

        # Show issues first (errors, warnings), then infos
        def _sort_key(r):
            lvl = (r.level or "INFO").upper()
            pri = {"ERROR": 0, "WARNING": 1, "INFO": 2}.get(lvl, 3)
            return (pri, r.code, r.relpath or "")

        for r in sorted(validation_results, key=_sort_key):
            lvl = (r.level or "INFO").upper()
            suffix = f" ({r.relpath})" if r.relpath else ""
            self.add_result(lvl, f"{r.code}: {r.message}{suffix}")

        # Keep some Day 2 extension info (top 8) for quick visibility
        self.add_result("INFO", "Top extensions:")
        shown = 0
        for ext, count in summary.extensions.items():
            if shown >= 8:
                remaining = len(summary.extensions) - shown
                if remaining > 0:
                    self.add_result("INFO", f"... +{remaining} more")
                break
            label = ext if ext else "(no_ext)"
            self.add_result("INFO", f"  - {label}: {count}")
            shown += 1

        self.log(f"Scanned {len(files)} files; validated {len(validation_results)} rule result(s).")
        self.log("---- SCAN DONE ----")

        # Enable next buttons later
        self.btn_package.setEnabled(True)
        self.btn_export.setEnabled(True)


