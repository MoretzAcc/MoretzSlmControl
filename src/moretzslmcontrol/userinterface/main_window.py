"""
Author: Moritz van Eimern
Date: 23.03.2026
"""

from __future__ import annotations

import logging
from html import escape
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QCloseEvent, QDoubleValidator, QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QApplication,
    QFormLayout,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSlider,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from moretzslmcontrol.monitor_stuff.models import SessionState
from moretzslmcontrol.hologram_manager import PatternSizeMismatchError
from moretzslmcontrol.util.bit_map_util import phaseToByte
from moretzslmcontrol.util.file_util import importBmpHologram, importNpyHologram
from moretzslmcontrol.util.pattern_modification import makeSlmPhaseForSingleFocalSpot

if TYPE_CHECKING:
    from moretzslmcontrol.monitor_stuff.models import SessionDebugView
    from moretzslmcontrol.monitor_stuff.monitor_manager import MonitorManager
    from moretzslmcontrol.monitor_stuff.platform.base import MonitorEdid

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Presentation-only control surface for the known SLM displays."""

    _MAX_ASSOCIATED_MONITORS = 3

    def __init__(self, monitor_manager: MonitorManager) -> None:
        super().__init__()
        self._monitor_manager = monitor_manager
        self._loaded_patterns: dict[str, dict[str, NDArray[np.float32]]] = {}
        self._loaded_pattern_paths: dict[str, dict[str, str]] = {}
        self._pattern_path_fields: dict[str, QLineEdit] = {}
        self._preview_labels: dict[str, QLabel] = {}
        self._shift_sliders: dict[str, QSlider] = {}
        self._shift_inputs: dict[str, QLineEdit] = {}
        self._modification_parameter_fields: dict[str, QLineEdit] = {}
        self._last_modification_parameters: dict[str, tuple[float, ...]] = {}
        self._pattern_active_checks: dict[str, QCheckBox] = {}
        self._pattern_flip_checks: dict[tuple[str, str], QCheckBox] = {}
        self._console_screen_uid: str | None = None
        self._monitor_manager.recordsChanged.connect(self.refresh_views)
        self._monitor_manager.consoleChanged.connect(self._on_console_changed)

        self.setWindowTitle("SLM Display Control")
        self.resize(1550, 880)
        self.setMinimumSize(1280, 780)

        self._list_widget = QListWidget()
        self._list_widget.setMinimumWidth(150)
        self._list_widget.setMaximumWidth(210)
        self._list_widget.currentItemChanged.connect(self._update_selected_screen)

        self._details_page = self._build_details_page()
        self._empty_page = self._build_empty_page()
        self._content_stack = QStackedWidget()
        self._content_stack.addWidget(self._empty_page)
        self._content_stack.addWidget(self._details_page)

        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 8, 12)
        sidebar_layout.addWidget(QLabel("Screens"))
        sidebar_layout.addWidget(self._list_widget)
        sidebar_layout.addWidget(QPushButton("Refresh"))

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)

        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 12, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(sidebar)
        main_layout.addWidget(separator)
        main_layout.addWidget(self._content_stack, 1)
        self.setCentralWidget(central_widget)

        self.refresh_views()

    def refresh_views(self) -> None:
        selected_screen_uid = self._selected_screen_uid()
        self._list_widget.clear()
        for view in self._monitor_manager.iter_debug_views():
            item = QListWidgetItem(self._build_item_label(view))
            item.setData(Qt.ItemDataRole.UserRole, view.screen_uid)
            item.setToolTip(self._build_item_tooltip(view))
            self._list_widget.addItem(item)
            if view.screen_uid == selected_screen_uid:
                self._list_widget.setCurrentItem(item)
        if self._list_widget.currentItem() is None and self._list_widget.count() > 0:
            self._list_widget.setCurrentRow(0)
        self._update_selected_screen()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Exit the application even when fullscreen SLM output windows remain open."""
        logger.info("Closing application")
        self._monitor_manager.shutdown()
        event.accept()
        QApplication.quit()

    def _build_empty_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 12, 24)
        empty_label = QLabel("Select a screen to view its information and settings.")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(empty_label)
        return page

    def _build_details_page(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(24, 20, 12, 20)
        page_layout.setSpacing(12)

        title_row = QHBoxLayout()
        self._screen_title = QLabel("Screen settings")
        self._screen_title.setStyleSheet("font-size: 20px; font-weight: 600;")
        self._slm_window_button = QPushButton()
        self._slm_window_button.setFixedHeight(52)
        self._slm_window_button.clicked.connect(self._toggle_slm_window)
        title_row.addWidget(self._screen_title)
        title_row.addStretch()
        page_layout.addLayout(title_row)

        information_row = QHBoxLayout()
        information_row.setSpacing(12)
        screen_information = self._build_screen_information_group()
        screen_information.setMinimumWidth(360)
        information_row.addWidget(screen_information)
        information_row.addWidget(self._build_monitor_information_group(), 1)
        page_layout.addLayout(information_row)
        page_layout.addWidget(self._build_pattern_group(), 2)
        page_layout.addWidget(self._build_console_group())
        return page

    def _build_screen_information_group(self) -> QGroupBox:
        group = QGroupBox("Screen information")
        layout = QFormLayout(group)
        self._screen_info_fields: dict[str, QLabel] = {}
        for key, label in (
            ("display_name", "Display name"),
            ("screen_name", "Screen name"),
            ("resolution", "Resolution"),
            ("screen_uid", "Screen UID"),
            ("heros_name", "Hero name"),
            ("screen_connection", "Screen connection"),
            ("slm_window", "SLM window"),
        ):
            value = self._new_information_label()
            value.setWordWrap(True)
            self._screen_info_fields[key] = value
            layout.addRow(f"{label}:", value)
        return group

    def _build_monitor_information_group(self) -> QGroupBox:
        group = QGroupBox("Associated monitors")
        layout = QHBoxLayout(group)
        self._no_associated_monitors_label = QLabel("No associated monitors detected")
        layout.addWidget(self._no_associated_monitors_label)
        self._associated_monitor_cards: list[QFrame] = []
        self._associated_monitor_titles: list[QLabel] = []
        self._associated_monitor_fields: list[dict[str, QLabel]] = []
        for index in range(self._MAX_ASSOCIATED_MONITORS):
            card = QFrame()
            card.setFrameShape(QFrame.Shape.StyledPanel)
            card.setMinimumWidth(250)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 6, 8, 6)
            title = QLabel(f"Monitor {index + 1}")
            title.setStyleSheet("font-weight: 600;")
            card_layout.addWidget(title)

            form = QFormLayout()
            form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            fields: dict[str, QLabel] = {}
            for key, label in (
                ("os_identifier", "OS identifier"),
                ("manufacturer", "Manufacturer"),
                ("product_id", "Product ID"),
                ("manufactured", "Year / Week"),
                ("name", "Name"),
                ("serial", "Serial"),
            ):
                value = self._new_information_label()
                value.setWordWrap(True)
                value.setMinimumWidth(145)
                fields[key] = value
                form.addRow(f"{label}:", value)
            card_layout.addLayout(form)
            card.hide()
            self._associated_monitor_cards.append(card)
            self._associated_monitor_titles.append(title)
            self._associated_monitor_fields.append(fields)
            layout.addWidget(card, 1)
        layout.addStretch()
        return group

    def _build_pattern_group(self) -> QGroupBox:
        group = QGroupBox("Pattern composition")
        layout = QHBoxLayout(group)
        layout.setSpacing(8)

        layout.addWidget(
            self._build_pattern_component(
                "Correction Pattern", component_key="base", has_file_selector=True
            ),
            1,
        )
        layout.addWidget(self._build_operator_label("+"))
        layout.addWidget(
            self._build_pattern_component("Hologram Pattern", component_key="hologram", has_file_selector=True),
            1,
        )
        layout.addWidget(self._build_operator_label("+"))
        layout.addWidget(
            self._build_pattern_component(
                "Modification Pattern", component_key="modification", has_shift_controls=True
            ),
            1,
        )
        layout.addWidget(self._build_operator_label("="))
        layout.addWidget(
            self._build_pattern_component("Applied Hologram", component_key="total"),
            1,
        )
        return group

    def _build_pattern_component(
        self,
        title: str,
        *,
        component_key: str | None = None,
        has_file_selector: bool = False,
        has_shift_controls: bool = False,
    ) -> QWidget:
        component = QWidget()
        layout = QVBoxLayout(component)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        preview = QLabel("Preview")
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setFixedHeight(90)
        preview.setStyleSheet("color: #d0d0d0;")
        if component_key is not None:
            self._preview_labels[component_key] = preview
        layout.addWidget(preview)

        if component_key != "total":
            enabled = QCheckBox("Active")
            enabled.setChecked(True)
            if component_key is not None:
                self._pattern_active_checks[component_key] = enabled
                enabled.toggled.connect(
                    lambda is_active, key=component_key: self._set_pattern_active(key, is_active)
                )
            layout.addWidget(enabled)
        else:
            layout.addSpacing(24)
            layout.addWidget(self._slm_window_button)

        if has_file_selector:
            if component_key is None:
                raise ValueError("A file selector requires a component key")
            file_row = QHBoxLayout()
            path = QLineEdit()
            path.setReadOnly(True)
            path.setPlaceholderText("No file")
            self._pattern_path_fields[component_key] = path
            file_row.addWidget(path, 1)
            file_button = QPushButton("File")
            file_button.clicked.connect(lambda: self._choose_pattern_file(component_key))
            file_row.addWidget(file_button)
            layout.addLayout(file_row)

            flip_row = QHBoxLayout()
            for direction, label in (("horizontal", "Flip horizontal"), ("vertical", "Flip vertical")):
                checkbox = QCheckBox(label)
                self._pattern_flip_checks[(component_key, direction)] = checkbox
                checkbox.toggled.connect(
                    lambda is_flipped, key=component_key, flip_direction=direction: self._set_pattern_flip(
                        key, flip_direction, is_flipped
                    )
                )
                flip_row.addWidget(checkbox)
            flip_row.addStretch()
            layout.addLayout(flip_row)

        if has_shift_controls:
            for axis in ("X", "Y", "Z"):
                layout.addLayout(self._build_shift_row(axis))
            layout.addLayout(self._build_modification_parameter_fields())

        layout.addStretch()
        return component

    @staticmethod
    def _build_operator_label(symbol: str) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addSpacing(20)
        operator = QLabel(symbol)
        operator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        operator.setFixedHeight(90)
        operator.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(operator)
        layout.addStretch()
        return container

    def _choose_pattern_file(self, component_key: str) -> None:
        component_name = {"base": "base aberration", "hologram": "hologram"}[component_key]
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select {component_name} file",
            "",
            "Hologram files (*.npy *.bmp)",
        )
        if not file_path:
            return

        try:
            suffix = Path(file_path).suffix.lower()
            if suffix == ".npy":
                pattern = importNpyHologram(file_path)
            elif suffix == ".bmp":
                pattern = importBmpHologram(file_path)
            else:
                raise ValueError("Only .npy and .bmp files are supported")
        except Exception as error:
            self._write_console(f"Error importing {component_name}: {error}")
            return

        screen_uid = self._selected_screen_uid()
        if screen_uid is None:
            self._write_console(f"Error importing {component_name}: no screen is selected")
            return
        self._loaded_patterns.setdefault(screen_uid, {})[component_key] = pattern
        self._loaded_pattern_paths.setdefault(screen_uid, {})[component_key] = file_path
        path_field = self._pattern_path_fields[component_key]
        path_field.setText(Path(file_path).name)
        path_field.setToolTip(file_path)
        self._upload_pattern(component_key, component_name, pattern, screen_uid)

    def _upload_pattern(
        self,
        component_key: str,
        component_name: str,
        pattern: NDArray[np.float32],
        screen_uid: str,
    ) -> None:
        displayer = self._monitor_manager.ensure_displayer(screen_uid)
        if displayer is None:
            self._write_console(f"Error applying {component_name}: screen is no longer available")
            return

        try:
            if component_key == "base":
                displayer.setCorrectionPattern(pattern)
            else:
                displayer.setHologramPattern(pattern)
        except PatternSizeMismatchError:
            return
        except Exception as error:
            self._write_console(f"Error applying {component_name}: {error}")
            return

        self.updatePreview()

    def _set_pattern_active(self, component_key: str, is_active: bool) -> None:
        screen_uid = self._selected_screen_uid()
        if screen_uid is None:
            return
        displayer = self._monitor_manager.ensure_displayer(screen_uid)
        if displayer is None:
            self._write_console("Error: selected screen is no longer available")
            return

        if component_key == "base":
            displayer.enableCorrectionPattern(is_active, update=False)
        elif component_key == "hologram":
            displayer.enableHologramPattern(is_active, update=False)
        elif component_key == "modification":
            displayer.enableModificationPattern(is_active, update=False)
        else:
            raise ValueError(f"Unknown pattern component: {component_key}")

        self.updatePreview()
        Thread(target=displayer.publishCurrentPattern, daemon=True).start()

    def _set_pattern_flip(self, component_key: str, direction: str, is_flipped: bool) -> None:
        screen_uid = self._selected_screen_uid()
        if screen_uid is None:
            return
        displayer = self._monitor_manager.ensure_displayer(screen_uid)
        if displayer is None:
            self._write_console("Error: selected screen is no longer available")
            return

        if component_key == "base":
            setter = (
                displayer.setFlipCorrectionPatternHorizontally
                if direction == "horizontal"
                else displayer.setFlipCorrectionPatternVertically
            )
        elif component_key == "hologram":
            setter = (
                displayer.setFlipHologramPatternHorizontally
                if direction == "horizontal"
                else displayer.setFlipHologramPatternVertically
            )
        else:
            raise ValueError(f"Unsupported flip component: {component_key}")

        setter(is_flipped, update=False)
        Thread(target=displayer.publishCurrentPattern, daemon=True).start()

    def updatePreview(self) -> None:
        """Update the bounded grayscale previews for the selected screen's patterns."""
        screen_uid = self._selected_screen_uid()
        displayer = self._monitor_manager.get_displayer(screen_uid) if screen_uid else None
        if displayer is None:
            for preview in self._preview_labels.values():
                preview.clear()
                preview.setText("Preview")
            return

        patterns = dict(
            zip(
                ("base", "hologram", "modification", "total"),
                displayer.getPatternSnapshots(),
                strict=True,
            )
        )
        correction_active, hologram_active, modification_active = displayer.getPatternInclusion()
        active_by_component = {
            "base": correction_active,
            "hologram": hologram_active,
            "modification": modification_active,
            "total": True,
        }
        for component_key, pattern in patterns.items():
            self._set_preview_image(
                self._preview_labels[component_key], pattern, active=active_by_component[component_key]
            )

    @staticmethod
    def _set_preview_image(
        preview: QLabel, pattern: NDArray[np.float32], *, active: bool = True
    ) -> None:
        height, width = pattern.shape
        max_width = max(1, min(preview.width(), 240))
        max_height = max(1, min(preview.height(), 90))
        scale = min(max_width / width, max_height / height, 1.0)
        target_width = max(1, round(width * scale))
        target_height = max(1, round(height * scale))
        row_indices = np.linspace(0, height - 1, target_height, dtype=np.intp)
        column_indices = np.linspace(0, width - 1, target_width, dtype=np.intp)
        if active:
            preview_phase = np.ascontiguousarray(pattern[row_indices][:, column_indices], dtype=np.float32)
            preview_bytes = phaseToByte(preview_phase)
        else:
            preview_bytes = np.full((target_height, target_width), 128, dtype=np.uint8)
        image = QImage(
            preview_bytes.data,
            target_width,
            target_height,
            preview_bytes.strides[0],
            QImage.Format.Format_Grayscale8,
        ).copy()
        preview.setPixmap(QPixmap.fromImage(image))

    def _write_console(self, message: str) -> None:
        screen_uid = self._selected_screen_uid()
        if screen_uid is None:
            logger.error(message)
            return
        level, clean_message = self._console_level_and_message(message)
        self._monitor_manager.write_to_console(screen_uid, clean_message, level)

    @staticmethod
    def _console_level_and_message(message: str) -> tuple[str, str]:
        for prefix, level in (("Error:", "error"), ("Warning:", "warning")):
            if message.startswith(prefix):
                return level, message.removeprefix(prefix).strip()
        return "info", message

    @Slot(str)
    def _on_console_changed(self, screen_uid: str) -> None:
        if screen_uid != self._selected_screen_uid():
            return
        self._show_console_for_screen(screen_uid, force=True)

    def _show_console_for_screen(self, screen_uid: str, *, force: bool = False) -> None:
        if not force and self._console_screen_uid == screen_uid:
            return
        self._console.clear()
        for level, message in self._monitor_manager.get_console_entries(screen_uid):
            self._append_console_entry(level, message)
        self._console_screen_uid = screen_uid

    def _append_console_entry(self, level: str, message: str) -> None:
        color = {"error": "#d32f2f", "warning": "#ef6c00", "info": "#2e7d32"}.get(level, "#2e7d32")
        self._console.append(f'<span style="color: {color};">{escape(message)}</span>')

    def _build_shift_row(self, axis: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(4)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(-200, 200)
        value_input = QLineEdit("0")
        value_input.setMaximumWidth(46)
        value_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        value_input.setValidator(QDoubleValidator(value_input))
        unit_label = QLabel("µm")
        self._shift_sliders[axis] = slider
        self._shift_inputs[axis] = value_input
        slider.sliderReleased.connect(lambda selected_axis=axis: self._on_shift_slider_released(selected_axis))
        value_input.editingFinished.connect(
            lambda selected_axis=axis: self._on_shift_input_edited(selected_axis)
        )
        row.addWidget(QLabel(f"{axis}:"))
        row.addWidget(slider, 1)
        row.addWidget(value_input)
        row.addWidget(unit_label)
        return row

    def _build_modification_parameter_fields(self) -> QFormLayout:
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        for key, label, default_value, unit, _tooltip in (
            (
                "max_shift",
                "Slider max shift",
                "200",
                "µm",
                "Sets the X, Y, and Z slider range. It does not change the generated pattern by itself.",
            ),
            (
                "wavelength",
                "Wavelength",
                "850",
                "nm",
                "Wavelength of the light used by the SLM system.",
            ),
            (
                "focal_length",
                "Focal length",
                "20",
                "mm",
                "Focal length of the objective lens.",
            ),
            (
                "magnification",
                "Magnification",
                "2",
                "",
                "Unitless magnification of the telescope between SLM and objective.",
            ),
            (
                "pixel_pitch",
                "Pixel pitch",
                "8",
                "µm",
                "Physical SLM pixel pitch; used as both dx and dy for the phase calculation.",
            ),
        ):
            field = QLineEdit(default_value)
            field.setMaximumWidth(70)
            field.setAlignment(Qt.AlignmentFlag.AlignRight)
            field.setValidator(QDoubleValidator(field))
            self._modification_parameter_fields[key] = field
            if key == "max_shift":
                field.editingFinished.connect(self._on_max_shift_edited)
            else:
                field.editingFinished.connect(self._update_modification_pattern)
            field_row = QWidget()
            field_layout = QHBoxLayout(field_row)
            field_layout.setContentsMargins(0, 0, 0, 0)
            field_layout.setSpacing(4)
            field_layout.addWidget(field)
            if unit:
                field_layout.addWidget(QLabel(unit))
            field_layout.addStretch()
            form.addRow(f"{label}:", field_row)
        return form

    def _on_shift_slider_released(self, axis: str) -> None:
        value = self._shift_sliders[axis].value()
        input_field = self._shift_inputs[axis]
        input_field.blockSignals(True)
        input_field.setText(str(value))
        input_field.blockSignals(False)
        self._update_modification_pattern()

    def _on_shift_input_edited(self, axis: str) -> None:
        try:
            value = float(self._shift_inputs[axis].text())
            maximum_shift = self._read_positive_modification_parameter("max_shift")
        except ValueError as error:
            self._write_console(f"Error: invalid {axis} shift: {error}")
            return

        clamped_value = max(-maximum_shift, min(maximum_shift, value))
        input_field = self._shift_inputs[axis]
        input_field.setText(self._format_number(clamped_value))
        slider = self._shift_sliders[axis]
        slider.blockSignals(True)
        slider.setValue(round(clamped_value))
        slider.blockSignals(False)
        self._update_modification_pattern()

    def _on_max_shift_edited(self) -> None:
        try:
            maximum_shift = self._read_positive_modification_parameter("max_shift")
        except ValueError as error:
            self._write_console(f"Error: invalid slider max shift: {error}")
            return

        try:
            current_values = {
                axis: float(input_field.text()) for axis, input_field in self._shift_inputs.items()
            }
        except ValueError as error:
            self._write_console(f"Error: invalid shift value: {error}")
            return

        slider_limit = round(maximum_shift)
        for axis, slider in self._shift_sliders.items():
            slider.blockSignals(True)
            slider.setRange(-slider_limit, slider_limit)
            slider.blockSignals(False)
            current_value = current_values[axis]
            clamped_value = max(-maximum_shift, min(maximum_shift, current_value))
            self._shift_inputs[axis].setText(self._format_number(clamped_value))
            slider.blockSignals(True)
            slider.setValue(round(clamped_value))
            slider.blockSignals(False)
        self._update_modification_pattern()

    def _update_modification_pattern(self) -> None:
        screen_uid = self._selected_screen_uid()
        if screen_uid is None:
            return

        try:
            x = float(self._shift_inputs["X"].text())
            y = float(self._shift_inputs["Y"].text())
            z = float(self._shift_inputs["Z"].text())
            wavelength = self._read_positive_modification_parameter("wavelength")
            focal_length = self._read_positive_modification_parameter("focal_length")
            magnification = self._read_positive_modification_parameter("magnification")
            pixel_pitch = self._read_positive_modification_parameter("pixel_pitch")
        except ValueError as error:
            self._write_console(f"Error: invalid modification parameter: {error}")
            return

        parameters = (x, y, z, wavelength, focal_length, magnification, pixel_pitch)
        if self._last_modification_parameters.get(screen_uid) == parameters:
            return

        displayer = self._monitor_manager.ensure_displayer(screen_uid)
        if displayer is None:
            self._write_console("Error: selected screen is no longer available")
            return
        height, width = displayer.shape
        try:
            pattern = makeSlmPhaseForSingleFocalSpot(
                x=x * 1e-6,
                y=y * 1e-6,
                z=z * 1e-6,
                wavelength=wavelength * 1e-9,
                f_objective=focal_length * 1e-3,
                magnification=magnification,
                Nx=width,
                Ny=height,
                dx=pixel_pitch * 1e-6,
                dy=pixel_pitch * 1e-6,
            )
            displayer.setModificationPattern(pattern)
        except PatternSizeMismatchError:
            return
        except Exception as error:
            self._write_console(f"Error: could not generate modification pattern: {error}")
            return

        self._last_modification_parameters[screen_uid] = parameters
        self.updatePreview()

    def _read_positive_modification_parameter(self, key: str) -> float:
        value = float(self._modification_parameter_fields[key].text())
        if value <= 0:
            raise ValueError(f"{key.replace('_', ' ')} must be greater than zero")
        return value

    @staticmethod
    def _format_number(value: float) -> str:
        return f"{value:g}"

    def _build_console_group(self) -> QGroupBox:
        group = QGroupBox("Console")
        layout = QVBoxLayout(group)
        self._console = QTextEdit()
        self._console.setReadOnly(True)
        self._console.setPlaceholderText("Nothing to show yet.")
        self._console.setFixedHeight(78)
        layout.addWidget(self._console)
        return group

    @staticmethod
    def _new_information_label() -> QLabel:
        label = QLabel("—")
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        return label

    def _update_selected_screen(self, *_: object) -> None:
        screen_uid = self._selected_screen_uid()
        if screen_uid is None:
            self._content_stack.setCurrentWidget(self._empty_page)
            return

        views = {view.screen_uid: view for view in self._monitor_manager.iter_debug_views()}
        view = views.get(screen_uid)
        if view is None:
            self._content_stack.setCurrentWidget(self._empty_page)
            return

        self._content_stack.setCurrentWidget(self._details_page)
        self._screen_title.setText(view.display_name or "Unnamed screen")
        self._update_slm_window_button(view.state)
        record = self._monitor_manager.get_screen_record(screen_uid)
        associated_monitors = record.associated_monitors if record is not None else []
        self._no_associated_monitors_label.setVisible(not associated_monitors)
        for index, card in enumerate(self._associated_monitor_cards):
            if index < len(associated_monitors):
                self._set_associated_monitor_card(index, associated_monitors[index])
                card.show()
            else:
                card.hide()
        pattern_paths = self._loaded_pattern_paths.get(screen_uid, {})
        for component_key, path_field in self._pattern_path_fields.items():
            file_path = pattern_paths.get(component_key, "")
            path_field.setText(Path(file_path).name if file_path else "")
            path_field.setToolTip(file_path)
        for key, value in {
            "display_name": view.display_name or "—",
            "screen_name": view.screen_name or "—",
            "resolution": view.resolution,
            "screen_uid": view.screen_uid,
            "heros_name": view.heros_name or "—",
            "screen_connection": self._screen_connection_text(view.state),
            "slm_window": self._slm_window_text(view.state),
        }.items():
            self._screen_info_fields[key].setText(value)
        self._sync_pattern_active_checks(screen_uid)
        self._sync_pattern_flip_checks(screen_uid)
        self._show_console_for_screen(screen_uid)
        self.updatePreview()

    def _sync_pattern_active_checks(self, screen_uid: str) -> None:
        displayer = self._monitor_manager.get_displayer(screen_uid)
        inclusion = displayer.getPatternInclusion() if displayer is not None else (True, True, True)
        for component_key, is_active in zip(
            ("base", "hologram", "modification"), inclusion, strict=True
        ):
            checkbox = self._pattern_active_checks[component_key]
            checkbox.blockSignals(True)
            checkbox.setChecked(is_active)
            checkbox.blockSignals(False)

    def _sync_pattern_flip_checks(self, screen_uid: str) -> None:
        displayer = self._monitor_manager.get_displayer(screen_uid)
        flip_states = (
            displayer.getPatternFlipStates() if displayer is not None else (False, False, False, False, False, False)
        )
        states_by_control = dict(
            zip(
                (
                    ("base", "horizontal"),
                    ("base", "vertical"),
                    ("hologram", "horizontal"),
                    ("hologram", "vertical"),
                    ("modification", "horizontal"),
                    ("modification", "vertical"),
                ),
                flip_states,
                strict=True,
            )
        )
        for control, checkbox in self._pattern_flip_checks.items():
            checkbox.blockSignals(True)
            checkbox.setChecked(states_by_control[control])
            checkbox.blockSignals(False)

    def _set_associated_monitor_card(self, index: int, monitor: MonitorEdid) -> None:
        edid = monitor.parsed_edid
        self._associated_monitor_titles[index].setText(f"Monitor {index + 1}")
        fields = self._associated_monitor_fields[index]
        fields["os_identifier"].setText(monitor.os_identifier or "—")
        fields["manufacturer"].setText(
            f"{edid.manufacturer or '—'} ({edid.manufacturer_pnp_id or '—'})"
        )
        fields["product_id"].setText(str(edid.product_id))
        fields["manufactured"].setText(f"{edid.year}/{edid.week}")
        fields["name"].setText(edid.name or "—")
        fields["serial"].setText(str(edid.serial) if edid.serial is not None else "—")

    @staticmethod
    def _screen_connection_text(state: SessionState) -> str:
        if state in (SessionState.INACTIVE_CONNECTED, SessionState.ACTIVE_CONNECTED):
            return "Connected"
        return "Disconnected"

    @staticmethod
    def _slm_window_text(state: SessionState) -> str:
        if MainWindow._is_slm_window_enabled(state):
            return "Enabled"
        return "Disabled"

    def _update_slm_window_button(self, state: SessionState) -> None:
        if self._is_slm_window_enabled(state):
            self._slm_window_button.setText("SLM WINDOW ON  —  Disable")
            self._slm_window_button.setStyleSheet(
                "background-color: #1565c0; color: white; font-weight: 700; border-radius: 4px;"
            )
        else:
            self._slm_window_button.setText("SLM WINDOW OFF  —  Enable")
            self._slm_window_button.setStyleSheet(
                "background-color: #b71c1c; color: white; font-weight: 700; border-radius: 4px;"
            )

    @staticmethod
    def _is_slm_window_enabled(state: SessionState) -> bool:
        return state in (SessionState.ACTIVE_CONNECTED, SessionState.ACTIVE_DISCONNECTED)

    def _toggle_slm_window(self) -> None:
        screen_uid = self._selected_screen_uid()
        if screen_uid is None:
            self._write_console("Error: select a screen before changing the SLM window")
            return

        session = self._monitor_manager.get_session(screen_uid)
        if session is not None and self._is_slm_window_enabled(session.state):
            self._monitor_manager.deactivate_monitor(screen_uid)
            self._write_console("SLM window disabled.")
            return

        if self._monitor_manager.activate_monitor(screen_uid) is None:
            self._write_console("Error: the selected screen is no longer available")
            return
        self._write_console("SLM window enabled.")

    def _selected_screen_uid(self) -> str | None:
        item = self._list_widget.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    @staticmethod
    def _build_item_label(view: SessionDebugView) -> str:
        return view.display_name or view.screen_name or view.screen_uid

    @staticmethod
    def _build_item_tooltip(view: SessionDebugView) -> str:
        return f"{view.resolution} | {view.screen_uid} | {SessionState.to_string(view.state)}"
