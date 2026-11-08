from __future__ import annotations

import signal
import subprocess
import sys
import unittest


@unittest.skipIf(sys.platform == 'win32', 'Unix signal delivery is verified on Linux')
class ApplicationSignalsTest(unittest.TestCase):
    def test_idle_qt_event_loop_processes_external_sigterm(self) -> None:
        code = '''
from moretzslmcontrol.app import _install_signal_handlers
from moretzslmcontrol.util.shutdown_reason import ShutdownReason
from PySide6.QtWidgets import QApplication
app = QApplication(['signal-test', '-platform', 'offscreen'])
_install_signal_handlers(app, ShutdownReason())
print('READY', flush=True)
raise SystemExit(app.exec())
'''
        process = subprocess.Popen([sys.executable, '-c', code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.assertEqual(process.stdout.readline().strip(), 'READY')
            process.send_signal(signal.SIGTERM)
            _, stderr = process.communicate(timeout=3)
            self.assertEqual(process.returncode, 128+signal.SIGTERM, stderr)
        finally:
            if process.poll() is None:
                process.kill()
            process.communicate()
