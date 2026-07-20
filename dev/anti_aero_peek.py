import ctypes
import sys

from PySide6.QtWidgets import QApplication, QMainWindow


DWMWA_EXCLUDED_FROM_PEEK = 12


def exclude_from_aero_peek(widget, excluded=True):
    if sys.platform != "win32":
        return

    # Erzwingt die Erzeugung des nativen Windows-Fensters.
    hwnd = int(widget.winId())

    value = ctypes.c_int(1 if excluded else 0)

    result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
        ctypes.c_void_p(hwnd),
        ctypes.c_uint(DWMWA_EXCLUDED_FROM_PEEK),
        ctypes.byref(value),
        ctypes.sizeof(value),
    )

    if result != 0:
        raise OSError(f"DwmSetWindowAttribute fehlgeschlagen: HRESULT {result:#x}")


class MainWindow(QMainWindow):
    def showEvent(self, event):
        super().showEvent(event)
        exclude_from_aero_peek(self)


app = QApplication(sys.argv)

window = MainWindow()
window.resize(800, 500)
window.show()

sys.exit(app.exec())