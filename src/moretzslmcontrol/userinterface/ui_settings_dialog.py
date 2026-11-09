"""Modeless UI scaling controls with immediate application and persistence."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLabel, QVBoxLayout, QWidget

from moretzslmcontrol.util.ui_settings import UiSettings


class UiSettingsDialog(QDialog):
    settingsChanged = Signal(object)

    def __init__(self, settings: UiSettings, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle("UI settings")
        self.setFont(QApplication.font())
        self.setWindowModality(Qt.WindowModality.NonModal)
        layout = QVBoxLayout(self)
        explanation = QLabel("Changes apply immediately and are saved automatically.\nEffective scale = global scale * relative factor.")
        layout.addWidget(explanation)
        form = QFormLayout()
        self.fields: dict[str, QDoubleSpinBox] = {}
        for key, title in (("global_scale", "Global scale"), ("font_scale", "Font size (relative)"),
                           ("element_scale", "UI elements (relative)"), ("preview_scale", "Previews (relative)")):
            field = QDoubleSpinBox()
            field.setRange(25, 300)
            field.setDecimals(0)
            field.setSingleStep(5)
            field.setSuffix(" %")
            field.setKeyboardTracking(True)
            field.setValue(settings.to_dict()[key] * 100)
            field.valueChanged.connect(self._changed)
            self.fields[key] = field
            form.addRow(title, field)
        layout.addLayout(form)
        self._effective_label = QLabel()
        layout.addWidget(self._effective_label)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.RestoreDefaults | QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self._restore_defaults)
        buttons.rejected.connect(self.close)
        layout.addWidget(buttons)
        self.set_settings(settings)

    def set_settings(self, settings: UiSettings) -> None:
        for key, value in settings.to_dict().items():
            field = self.fields[key]
            field.blockSignals(True)
            field.setValue(value * 100)
            field.blockSignals(False)
        self._effective_label.setText(
            f"Effective: font {settings.global_scale * settings.font_scale:.0%}, "
            f"elements {settings.global_scale * settings.element_scale:.0%}, "
            f"previews {settings.global_scale * settings.preview_scale:.0%}"
        )

    def _changed(self) -> None:
        settings = UiSettings(**{key: field.value() / 100 for key, field in self.fields.items()})
        self.set_settings(settings)
        self.settingsChanged.emit(settings)

    def _restore_defaults(self) -> None:
        settings = UiSettings()
        self.set_settings(settings)
        self.settingsChanged.emit(settings)
