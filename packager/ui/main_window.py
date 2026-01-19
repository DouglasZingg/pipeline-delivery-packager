import os

from PySide6.QtCore import Qt, QObject, QThread, Signal
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
    QProgressBar,
)

from packager.core.scanner import scan_folder
from packager.core.profiles import get_profile
from packager.core.validator import validate_delivery
from packager.core.planner import build_pack_plan
from packager.core.pack import execute_pack
from packager.core.manifest import build_manifest_dict, write_manifest_json


class PackWorker(QObject):
    progress = Signal(int, int, str)   # current, total, message
    finished = Signal(object, object)  # summary, issues

    def __init__(self, plan, overwrite=False):
        super().__init__()
        self.plan = plan
        self.overwrite = overwrite
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        def _is_cancelled():
            return self._cancelled

        def _progress(i, total, item):
            msg = f"{i}/{total}  {item.relpath} -> {item.category}/"
            self.progress.emit(i, total, msg)

        summary, issues = execute_pack(
            plan=self.plan,
            overwrite=self.overwrite,
            progress_cb=_progress,
            is_cancelled=_is_cancelled,
        )
        self.finished.emit(summary, issues)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline Delivery Packager (v0.5)")
        self.setMinimumSize(1020, 680)

        # State
        self._last_plan = []
        self._last_files = []
        self._last_summary = None
        self._last_validation = []
        self._pack_thread = None
        self._pack_worker = None

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
        # Project / Asset / Version
        # -------------------------
        proj_row = QHBoxLayout()

        self.project_edit = QLineEdit()
        self.project_edit.setPlaceholderText("ProjectName (e.g. MyShow / MyGame)")
        self.project_edit.setText("ProjectName")

        self.asset_edit = QLineEdit()
        self.asset_edit.setPlaceholderText("AssetName (e.g. CrateA)")
        self.asset_edit.setText("AssetName")

        self.version_edit = QLineEdit()
        self.version_edit.setPlaceholderText("v001")
        self.version_edit.setText("v001")
        self.version_edit.setMaximumWidth(120)

        proj_row.addWidget(QLabel("Project:"))
        proj_row.addWidget(self.project_edit, 1)
        proj_row.addWidget(QLabel("Asset:"))
        proj_row.addWidget(self.asset_edit, 1)
        proj_row.addWidget(QLabel("Version:"))
        proj_row.addWidget(self.version_edit)

        main_layout.addLayout(proj_row)

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

        self.btn_preview = QPushButton("Preview")
        self.btn_preview.clicked.connect(self.on_preview_clicked)

        self.btn_package = QPushButton("Package")
        self.btn_package.clicked.connect(self.on_package_execute_clicked)

        self.btn_export = QPushButton("Export Report")
        self.btn_export.setEnabled(False)  # enabled after Preview
        self.btn_export.clicked.connect(self.on_export_manifest_clicked)

        mid_row.addWidget(self.btn_scan)
        mid_row.addWidget(self.btn_preview)
        mid_row.addWidget(self.btn_package)
        mid_row.addWidget(self.btn_export)

        main_layout.addLayout(mid_row)

        # -------------------------
        # Progress + Cancel (Day 5)
        # -------------------------
        prog_row = QHBoxLayout()

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.on_cancel_clicked)

        prog_row.addWidget(QLabel("Progress:"))
        prog_row.addWidget(self.progress, 1)
        prog_row.addWidget(self.btn_cancel)

        main_layout.addLayout(prog_row)

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
        splitter.setSizes([600, 420])

        main_layout.addWidget(splitter, 1)

        self.log("Ready. Choose folders, then Scan / Preview / Package.")

        # Optional: stable IDs (useful for UI tests later)
        self.input_edit.setObjectName("input_edit")
        self.output_edit.setObjectName("output_edit")
        self.project_edit.setObjectName("project_edit")
        self.asset_edit.setObjectName("asset_edit")
        self.version_edit.setObjectName("version_edit")
        self.btn_scan.setObjectName("btn_scan")
        self.btn_preview.setObjectName("btn_preview")
        self.btn_package.setObjectName("btn_package")
        self.btn_cancel.setObjectName("btn_cancel")
        self.results_list.setObjectName("results_list")
        self.log_box.setObjectName("log_box")
        self.progress.setObjectName("progress")

    # -------------------------
    # UI Helpers
    # -------------------------
    def log(self, msg: str):
        self.log_box.appendPlainText(msg)

    def add_result(self, level: str, message: str):
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

    def _require_paths(self):
        input_path = self.input_edit.text().strip()
        output_path = self.output_edit.text().strip()

        if not input_path or not os.path.isdir(input_path):
            QMessageBox.warning(self, "Missing Input", "Please choose a valid input folder.")
            return None, None

        if not output_path or not os.path.isdir(output_path):
            QMessageBox.warning(self, "Missing Output", "Please choose a valid output folder.")
            return None, None

        return input_path, output_path

    def _scan_current(self):
        input_path, _ = self._require_paths()
        if not input_path:
            return None

        ignore_dirs = {".git", "__pycache__", ".venv", "node_modules"}
        files, summary = scan_folder(
            input_path,
            ignore_dirs=ignore_dirs,
            ignore_hidden=True,
            follow_symlinks=False,
        )
        return files, summary

    # -------------------------
    # Scan (Day 3)
    # -------------------------
    def on_scan_clicked(self):
        self.results_list.clear()
        self._last_plan = []

        input_path, output_path = self._require_paths()
        if not input_path:
            return

        profile_name = self.profile_combo.currentText()

        self.log("---- SCAN START ----")
        self.log(f"Profile: {profile_name}")
        self.log(f"Input:   {input_path}")
        self.log(f"Output:  {output_path}")

        try:
            scanned = self._scan_current()
            if not scanned:
                return
            files, summary = scanned
        except Exception as e:
            self.add_result("ERROR", f"Scan failed: {e}")
            self.log(f"ERROR: {e}")
            return

        mb = summary.total_bytes / (1024 * 1024) if summary.total_bytes else 0.0
        self.add_result("INFO", f"Scan OK: {summary.total_files} files in {summary.total_dirs} folders ({mb:.2f} MB)")
        self.add_result("INFO", f"Unique extensions: {len(summary.extensions)}")

        profile = get_profile(profile_name)
        validation_results = validate_delivery(
            input_root=input_path,
            files=files,
            summary=summary,
            profile=profile,
        )

        counts = {"ERROR": 0, "WARNING": 0, "INFO": 0}
        for r in validation_results:
            lvl = (r.level or "INFO").upper()
            counts[lvl] = counts.get(lvl, 0) + 1

        self.add_result("INFO", f"Validation: {counts.get('ERROR', 0)} error(s), {counts.get('WARNING', 0)} warning(s)")

        def _sort_key(r):
            lvl = (r.level or "INFO").upper()
            pri = {"ERROR": 0, "WARNING": 1, "INFO": 2}.get(lvl, 3)
            return (pri, r.code, r.relpath or "")

        for r in sorted(validation_results, key=_sort_key):
            lvl = (r.level or "INFO").upper()
            suffix = f" ({r.relpath})" if r.relpath else ""
            self.add_result(lvl, f"{r.code}: {r.message}{suffix}")

        self._last_files = files
        self._last_summary = summary
        self._last_validation = validation_results

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

        self.log(f"Scanned {len(files)} files; validated {len(validation_results)} result(s).")
        self.log("---- SCAN DONE ----")

    # -------------------------
    # Preview (Day 4)
    # -------------------------
    def on_preview_clicked(self):
        self.results_list.clear()
        self._last_plan = []

        input_path, output_path = self._require_paths()
        if not input_path:
            return

        project = self.project_edit.text().strip()
        asset = self.asset_edit.text().strip()
        version = self.version_edit.text().strip()

        self.log("---- PREVIEW START ----")
        self.log(f"Project: {project} | Asset: {asset} | Version: {version}")

        try:
            scanned = self._scan_current()
            if not scanned:
                return
            files, summary = scanned
            # keep latest scan snapshot
            self._last_files = files
            self._last_summary = summary
            profile_name = self.profile_combo.currentText()
            profile = get_profile(profile_name)
            self._last_validation = validate_delivery(
                input_root=input_path,
                files=files,
                summary=summary,
                profile=profile,
            )
        except Exception as e:
            self.add_result("ERROR", f"Scan failed: {e}")
            self.log(f"ERROR: {e}")
            return

        plan, issues = build_pack_plan(
            files=files,
            output_root=output_path,
            project=project,
            asset=asset,
            version=version,
        )

        err_count = sum(1 for i in issues if i.level.upper() == "ERROR")
        warn_count = sum(1 for i in issues if i.level.upper() == "WARNING")
        info_count = sum(1 for i in issues if i.level.upper() == "INFO")

        if issues:
            self.add_result("INFO", f"Preview checks: {err_count} error(s), {warn_count} warning(s), {info_count} info")
            for i in issues:
                suffix = f" ({i.relpath})" if i.relpath else ""
                self.add_result(i.level, f"{i.code}: {i.message}{suffix}")

        if err_count > 0:
            self.add_result("ERROR", "Preview blocked due to errors.")
            self.log("---- PREVIEW BLOCKED ----")
            return

        by_cat = {}
        for item in plan:
            by_cat[item.category] = by_cat.get(item.category, 0) + 1

        self.add_result("INFO", f"Plan ready: {len(plan)} file(s) will be copied.")
        for cat, count in sorted(by_cat.items(), key=lambda kv: (-kv[1], kv[0])):
            self.add_result("INFO", f"  - {cat}: {count}")

        self.add_result("INFO", "Sample mappings (first 20):")
        for item in plan[:20]:
            self.add_result("INFO", f"{item.relpath}  ->  {item.category}/")
        if len(plan) > 20:
            self.add_result("INFO", f"... +{len(plan) - 20} more")

        self._last_plan = plan
        self.btn_export.setEnabled(True)
        self.add_result("INFO", "Preview OK. Click Package to copy files.")

        self.log(f"Preview plan contains {len(plan)} item(s).")
        self.log("---- PREVIEW DONE ----")

    # -------------------------
    # Package execute (Day 5)
    # -------------------------
    def on_package_execute_clicked(self):
        if not self._last_plan:
            QMessageBox.information(
                self,
                "No Preview Plan",
                "Click Preview first to generate a packaging plan (Day 4).",
            )
            return

        if len(self._last_plan) == 0:
            QMessageBox.information(self, "Empty Plan", "No files to package.")
            return

        self.progress.setValue(0)
        self.btn_cancel.setEnabled(True)

        # Lock buttons during pack
        self.btn_scan.setEnabled(False)
        self.btn_preview.setEnabled(False)
        self.btn_package.setEnabled(False)
        self.btn_export.setEnabled(False)

        self.log("---- PACKAGING START ----")
        self.add_result("INFO", f"Packaging {len(self._last_plan)} file(s)...")

        self._pack_thread = QThread()
        self._pack_worker = PackWorker(self._last_plan, overwrite=False)
        self._pack_worker.moveToThread(self._pack_thread)

        self._pack_thread.started.connect(self._pack_worker.run)
        self._pack_worker.progress.connect(self._on_pack_progress)
        self._pack_worker.finished.connect(self._on_pack_finished)

        # Cleanup
        self._pack_worker.finished.connect(self._pack_thread.quit)
        self._pack_worker.finished.connect(self._pack_worker.deleteLater)
        self._pack_thread.finished.connect(self._pack_thread.deleteLater)

        self._pack_thread.start()

    def _on_pack_progress(self, current: int, total: int, message: str):
        pct = int((current / max(total, 1)) * 100)
        self.progress.setValue(pct)
        # Keep log readable
        if pct % 10 == 0 or current == 1 or current == total:
            self.log(message)

    def _on_pack_finished(self, summary, issues):
        self.btn_cancel.setEnabled(False)

        # Unlock buttons
        self.btn_scan.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.btn_package.setEnabled(True)
        self.btn_export.setEnabled(True)

        self.add_result("INFO", f"Pack done: copied={summary.copied}, skipped={summary.skipped}, failed={summary.failed}")

        if issues:
            def _pri(i):
                lvl = i.level.upper()
                return {"ERROR": 0, "WARNING": 1, "INFO": 2}.get(lvl, 3)

            for i in sorted(issues, key=_pri):
                suffix = f" ({i.relpath})" if i.relpath else ""
                self.add_result(i.level, f"{i.code}: {i.message}{suffix}")

        # If everything copied cleanly, push progress to 100
        if summary.failed == 0:
            self.progress.setValue(100)

        self.log("---- PACKAGING DONE ----")

    def on_cancel_clicked(self):
        if self._pack_worker:
            self._pack_worker.cancel()
            self.log("Cancel requested...")
            self.add_result("WARNING", "Cancel requested...")

    def on_export_manifest_clicked(self):
        if not self._last_plan:
            QMessageBox.information(self, "Nothing to Export", "Run Preview first so the tool has a packaging plan.")
            return

        input_path, output_path = self._require_paths()
        if not input_path:
            return

        project = self.project_edit.text().strip()
        asset = self.asset_edit.text().strip()
        version = self.version_edit.text().strip()
        profile_name = self.profile_combo.currentText()

        # Destination for manifest inside delivery drop
        manifest_path = os.path.join(
            output_path,
            project,
            asset,
            version,
            "docs",
            "manifest.json",
        )

        # Use latest validation snapshot (from Scan or Preview)
        validation_results = self._last_validation or []

        manifest = build_manifest_dict(
            tool_name="Pipeline Delivery Packager",
            tool_version="1.0.0-dev",
            profile=profile_name,
            input_root=input_path,
            output_root=output_path,
            project=project,
            asset_name=asset,
            version=version,
            validation_results=validation_results,
            plan=self._last_plan,
            include_file_stats=True,
        )

        try:
            written = write_manifest_json(manifest, manifest_path)
        except Exception as e:
            self.add_result("ERROR", f"MANIFEST_WRITE_FAILED: {e}")
            QMessageBox.critical(self, "Export Failed", f"Failed to write manifest:\n{e}")
            return

        self.add_result("INFO", f"Manifest written: {written}")
        self.log(f"Manifest exported: {written}")
        QMessageBox.information(self, "Export Complete", f"Manifest exported:\n{written}")
