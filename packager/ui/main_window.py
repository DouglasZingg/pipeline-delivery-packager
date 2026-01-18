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
        Day 1 placeholder result item.
        Later we'll color-code severity properly.
        """
        text = f"[{level}] {message}"
        item = QListWidgetItem(text)
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
        profile = self.profile_combo.currentText()

        if not input_path or not os.path.isdir(input_path):
            QMessageBox.warning(self, "Missing Input", "Please choose a valid input folder.")
            return

        if not output_path or not os.path.isdir(output_path):
            QMessageBox.warning(self, "Missing Output", "Please choose a valid output folder.")
            return

        self.log("---- SCAN START ----")
        self.log(f"Profile: {profile}")
        self.log(f"Input:   {input_path}")
        self.log(f"Output:  {output_path}")

        # Day 1 = just confirm selections
        self.add_result("INFO", f"Input folder OK: {input_path}")
        self.add_result("INFO", f"Output folder OK: {output_path}")
        self.add_result("INFO", f"Profile selected: {profile}")
        self.add_result("INFO", "Scanner not implemented yet (Day 2).")

        self.log("---- SCAN DONE ----")

        # Enable next buttons later
        self.btn_package.setEnabled(True)
        self.btn_export.setEnabled(True)
