"""Desktop GUI smoke tests; requires requirements-gui.txt."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from PySide6.QtCore import QEventLoop, QProcess, QTimer
    from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
    from microstrip_gui import CalculatorWindow
except ImportError:
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 is not installed")
class CalculatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = CalculatorWindow()

    def tearDown(self):
        self.window.close()

    def run_calculation(self):
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        self.window.process.finished.connect(loop.quit)
        self.window.calculate()
        timer.start(120000)
        loop.exec()
        self.window.process.finished.disconnect(loop.quit)
        self.assertEqual(self.window.process.state(), QProcess.ProcessState.NotRunning)
        self.assertEqual(self.window.status.text(), "Calculation complete.")

    def test_default_vacuum_export_and_validation(self):
        self.run_calculation()
        self.assertAlmostEqual(self.window.result['characteristic_impedance_ohm'], 31.55849811, places=3)
        with tempfile.TemporaryDirectory() as directory:
            destination = str(Path(directory) / 'result.json')
            with patch.object(QFileDialog, 'getSaveFileName', return_value=(destination, '')):
                self.window._save('result.json', 'JSON files (*.json)')
            self.assertTrue(Path(destination).is_file())
        self.window.fields['er1'].setValue(1)
        self.window.fields['er2'].setValue(1)
        self.assertIsNone(self.window.result)
        self.run_calculation()
        self.assertAlmostEqual(self.window.result['characteristic_impedance_ohm'], 61.65455342, places=3)
        self.assertAlmostEqual(self.window.result['effective_permittivity'], 1.0, places=9)
        self.window.fields['trace_thickness'].setValue(self.window.fields['h2'].value())
        self.window.calculate()
        self.assertIn('smaller', self.window.status.text())

    def test_close_during_calculation(self):
        self.window.calculate()
        with patch.object(QMessageBox, 'warning') as warning:
            self.window.close()
        warning.assert_not_called()
        self.assertEqual(self.window.process.state(), QProcess.ProcessState.NotRunning)


if __name__ == '__main__':
    unittest.main()
