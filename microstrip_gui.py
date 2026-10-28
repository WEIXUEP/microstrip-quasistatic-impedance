#!/usr/bin/env python3
"""Desktop interface for the microstrip quasi-static FEM solver."""
from __future__ import annotations

import json
import math
from pathlib import Path
import shutil
import sys
import tempfile

from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QProgressBar, QPushButton, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget,
)

ROOT = Path(__file__).resolve().parent
FIELDS = (
    ("w1", "Bottom width W1", 10.0, " mil"),
    ("w2", "Top width W2", 5.6, " mil"),
    ("trace_thickness", "Trace thickness T", 1.8, " mil"),
    ("h1", "Lower height H1", 2.97, " mil"),
    ("er1", "Lower permittivity Er1", 4.2, ""),
    ("h2", "Upper height H2", 3.53, " mil"),
    ("er2", "Upper permittivity Er2", 4.2, ""),
    ("trace_mesh_area_factor", "Trace area factor", 50.0, ""),
    ("far_mesh_area_factor", "Far-field area factor", 400.0, ""),
)


class CalculatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Microstrip FEM Calculator")
        self.resize(1020, 760)
        self.setMinimumSize(640, 520)
        self.temp = tempfile.TemporaryDirectory(prefix="microstrip-fem-")
        self.output = Path(self.temp.name)
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._process_error)
        self.log = ""
        self.cancelled = False
        self.result = None
        self.fields = {}
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #f8fafb; color: #193246; font-size: 13px; }
            QGroupBox { border: 1px solid #cedce5; border-radius: 4px; margin-top: 10px; padding: 10px 10px 7px; font-weight: 600; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QDoubleSpinBox, QComboBox { background: white; border: 1px solid #b9cbd6; border-radius: 3px; padding: 3px; min-height: 19px; }
            QPushButton { border: 1px solid #afc3ce; border-radius: 3px; padding: 8px 14px; background: white; font-weight: 600; }
            QPushButton:hover { background: #e7f0f5; }
            QPushButton:disabled { color: #8597a1; background: #edf1f3; }
            QPushButton#calculate { background: #245d79; color: white; border-color: #245d79; }
            QPushButton#calculate:disabled { background: #9aaeb8; border-color: #9aaeb8; }
            QLabel#headline { font-size: 23px; font-weight: 700; }
            QLabel#impedance { font-size: 32px; font-weight: 700; color: #245d79; }
            QLabel#muted { color: #5d7686; }
            QProgressBar { border: 0; height: 4px; background: #e2ebf0; }
            QProgressBar::chunk { background: #3981a6; }
        """)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)
        content = QWidget()
        scroll.setWidget(content)
        outer = QVBoxLayout(content)
        outer.setContentsMargins(22, 16, 22, 18)
        heading = QLabel("Microstrip FEM calculator")
        heading.setObjectName("headline")
        outer.addWidget(heading)
        subtitle = QLabel("Two-layer, finite-ground quasi-static model. Dimensions are in mil.")
        subtitle.setWordWrap(True)
        subtitle.setObjectName("muted")
        outer.addWidget(subtitle)
        columns = QHBoxLayout()
        columns.setSpacing(20)
        outer.addLayout(columns)

        left = QVBoxLayout()
        columns.addLayout(left, 1)
        for title, start, end in (("Trace", 0, 3), ("Dielectric layers", 3, 7), ("Mesh", 7, 9)):
            group = QGroupBox(title)
            layout = QFormLayout(group)
            layout.setVerticalSpacing(5)
            layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            for key, label, default, suffix in FIELDS[start:end]:
                field = QDoubleSpinBox()
                field.setDecimals(6)
                field.setRange(0.000001, 1_000_000)
                field.setValue(default)
                field.setSuffix(suffix)
                field.setKeyboardTracking(False)
                field.valueChanged.connect(self._invalidate)
                self.fields[key] = field
                layout.addRow(label, field)
            if title == "Mesh":
                self.order = QComboBox()
                self.order.addItem("P2", 2)
                self.order.addItem("P1", 1)
                self.order.currentIndexChanged.connect(self._invalidate)
                layout.addRow("Finite element order", self.order)
            left.addWidget(group)

        actions = QHBoxLayout()
        self.calculate_button = QPushButton("Calculate")
        self.calculate_button.setObjectName("calculate")
        self.calculate_button.clicked.connect(self.calculate)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel)
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset)
        for button in (self.calculate_button, self.cancel_button, self.reset_button):
            actions.addWidget(button)
        actions.addStretch()
        left.addLayout(actions)
        self.status = QLabel("Ready")
        self.status.setWordWrap(True)
        self.status.setObjectName("muted")
        left.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.hide()
        left.addWidget(self.progress)
        left.addStretch()

        right = QVBoxLayout()
        columns.addLayout(right, 1)
        results = QGroupBox("Results")
        result_layout = QVBoxLayout(results)
        result_layout.addWidget(QLabel("Characteristic impedance"))
        self.impedance = QLabel("--")
        self.impedance.setObjectName("impedance")
        result_layout.addWidget(self.impedance)
        grid = QGridLayout()
        self.values = {}
        for row, (key, label) in enumerate((
            ("effective_permittivity", "Effective permittivity"),
            ("capacitance_F_per_m", "Capacitance"),
            ("vacuum_capacitance_F_per_m", "Vacuum capacitance"),
            ("inductance_H_per_m", "Inductance"),
            ("phase_velocity_m_per_s", "Phase velocity"),
            ("mesh", "Mesh"), ("dofs", "Degrees of freedom"),
        )):
            name = QLabel(label)
            name.setObjectName("muted")
            value = QLabel("--")
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.values[key] = value
            grid.addWidget(name, row, 0)
            grid.addWidget(value, row, 1)
        result_layout.addLayout(grid)
        export = QHBoxLayout()
        self.save_json_button = QPushButton("Save JSON")
        self.save_json_button.clicked.connect(lambda: self._save("result.json", "JSON files (*.json)"))
        self.save_mesh_button = QPushButton("Save mesh")
        self.save_mesh_button.clicked.connect(lambda: self._save("microstrip.msh", "Gmsh mesh (*.msh)"))
        for button in (self.save_json_button, self.save_mesh_button):
            button.setEnabled(False)
            export.addWidget(button)
        result_layout.addLayout(export)
        right.addWidget(results)
        diagram = QLabel()
        diagram.setAlignment(Qt.AlignmentFlag.AlignCenter)
        diagram.setMinimumHeight(190)
        diagram.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        pixmap = QPixmap(str(ROOT / "doc" / "microstrip_geometry.svg"))
        if not pixmap.isNull():
            diagram.setPixmap(pixmap.scaled(420, 260, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        right.addWidget(diagram)
        note = QLabel("Lossless quasi-static model. Check mesh and domain convergence for your application.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        right.addWidget(note)
        right.addStretch()

    def _invalidate(self, *_):
        if self.result is not None:
            self.result = None
            self._clear_results()
            self.status.setText("Inputs changed. Calculate again.")

    def _clear_results(self):
        self.impedance.setText("--")
        for label in self.values.values():
            label.setText("--")
        self.save_json_button.setEnabled(False)
        self.save_mesh_button.setEnabled(False)

    def _set_busy(self, busy):
        self.calculate_button.setEnabled(not busy)
        self.reset_button.setEnabled(not busy)
        self.cancel_button.setEnabled(busy)
        for field in self.fields.values():
            field.setEnabled(not busy)
        self.order.setEnabled(not busy)
        self.progress.setVisible(busy)

    def calculate(self):
        values = {key: field.value() for key, field in self.fields.items()}
        if any(not math.isfinite(value) or value <= 0 for value in values.values()):
            self.status.setText("All inputs must be positive and finite.")
            return
        if values["trace_thickness"] >= values["h2"]:
            self.status.setText("Trace thickness must be smaller than upper layer height H2.")
            return
        if max(values["w1"], values["w2"]) >= 30 * (values["h1"] + values["h2"]):
            self.status.setText("Trace width must be smaller than the substrate width.")
            return
        self.result = None
        self._clear_results()
        self.log = ""
        self.cancelled = False
        args = [str(ROOT / "microstrip_quasistatic.py")]
        for key, value in values.items():
            args.extend(("--" + key.replace("_", "-"), str(value)))
        args.extend(("--order", str(self.order.currentData()), "--output", str(self.output)))
        self._set_busy(True)
        self.status.setText("Generating mesh and solving electrostatic problems...")
        self.process.setWorkingDirectory(str(ROOT))
        self.process.start(sys.executable, args)

    def _read_output(self):
        self.log += bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")

    def _process_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self._set_busy(False)
            self.status.setText(f"Could not start the solver: {self.process.errorString()}")

    def _finished(self, exit_code, exit_status):
        self._read_output()
        self._set_busy(False)
        if self.cancelled:
            self.status.setText("Calculation canceled.")
            return
        if exit_status != QProcess.ExitStatus.NormalExit or exit_code != 0:
            self.status.setText("Calculation failed. Check the error details.")
            QMessageBox.warning(self, "Calculation failed", self.log[-6000:] or self.process.errorString())
            return
        try:
            self.result = json.loads((self.output / "result.json").read_text(encoding="utf-8"))
            r = self.result
            self.impedance.setText(f"{r['characteristic_impedance_ohm']:.4f} ohm")
            self.values["effective_permittivity"].setText(f"{r['effective_permittivity']:.5f}")
            self.values["capacitance_F_per_m"].setText(f"{r['capacitance_F_per_m'] * 1e12:.4f} pF/m")
            self.values["vacuum_capacitance_F_per_m"].setText(f"{r['vacuum_capacitance_F_per_m'] * 1e12:.4f} pF/m")
            self.values["inductance_H_per_m"].setText(f"{r['inductance_H_per_m'] * 1e9:.4f} nH/m")
            self.values["phase_velocity_m_per_s"].setText(f"{r['phase_velocity_m_per_s']:.5e} m/s")
            m = r["mesh"]
            self.values["mesh"].setText(f"{m['vertices']:,} vertices / {m['triangles']:,} triangles")
            self.values["dofs"].setText(f"{m['finite_element_dofs']:,}")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.result = None
            self._clear_results()
            self.status.setText(f"Could not read solver results: {exc}")
            return
        self.save_json_button.setEnabled(True)
        self.save_mesh_button.setEnabled(True)
        self.status.setText("Calculation complete.")

    def cancel(self):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.cancelled = True
            self.status.setText("Canceling...")
            self.process.kill()

    def reset(self):
        for key, _, default, _ in FIELDS:
            self.fields[key].setValue(default)
        self.order.setCurrentIndex(0)
        self.result = None
        self._clear_results()
        self.status.setText("Ready")

    def _save(self, name, file_filter):
        if self.result is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save result", name, file_filter)
        if path:
            try:
                shutil.copyfile(self.output / name, path)
                self.status.setText(f"Saved {path}")
            except OSError as exc:
                QMessageBox.warning(self, "Save failed", str(exc))

    def closeEvent(self, event):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.cancelled = True
            self.process.kill()
            self.process.waitForFinished(5000)
        self.temp.cleanup()
        super().closeEvent(event)


def main():
    app = QApplication.instance()
    owns_app = app is None
    if owns_app:
        app = QApplication(sys.argv)
    window = CalculatorWindow()
    window.show()
    # Keep a reference when launched in an existing Qt event loop, e.g. Spyder.
    app._microstrip_window = window
    if owns_app:
        return app.exec()
    return 0


if __name__ == "__main__":
    main()
