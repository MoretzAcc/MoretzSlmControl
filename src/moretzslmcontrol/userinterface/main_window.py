"""
Author: Moritz van Eimern
Date: 23.03.2026
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFileDialog,
    QFrame,
    QGridLayout,
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

if TYPE_CHECKING:
    from moretzslmcontrol.monitor_stuff.models import SessionDebugView
    from moretzslmcontrol.monitor_stuff.monitor_manager import MonitorManager


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
        self._monitor_manager.recordsChanged.connect(self.refresh_views)

        self.setWindowTitle("SLM Display Control")
        self.resize(1350, 880)
        self.setMinimumSize(1120, 780)

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
        selected_monitor_id = self._selected_monitor_id()
        self._list_widget.clear()
        for view in self._monitor_manager.iter_debug_views():
            item = QListWidgetItem(self._build_item_label(view))
            item.setData(Qt.ItemDataRole.UserRole, view.monitor_id)
            item.setToolTip(self._build_item_tooltip(view))
            self._list_widget.addItem(item)
            if view.monitor_id == selected_monitor_id:
                self._list_widget.setCurrentItem(item)
        if self._list_widget.currentItem() is None and self._list_widget.count() > 0:
            self._list_widget.setCurrentRow(0)
        self._update_selected_screen()

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
        self._screen_status = QLabel()
        title_row.addWidget(self._screen_title)
        title_row.addStretch()
        title_row.addWidget(self._screen_status)
        title_row.addWidget(QPushButton("Enable / disable SLM window"))
        page_layout.addLayout(title_row)

        information_row = QHBoxLayout()
        information_row.setSpacing(12)
        information_row.addWidget(self._build_screen_information_group(), 2)
        information_row.addWidget(self._build_monitor_information_group(), 3)
        information_row.addWidget(self._build_session_information_group(), 3)
        page_layout.addLayout(information_row)
        page_layout.addWidget(self._build_pattern_group(), 1)
        page_layout.addWidget(self._build_console_group())
        return page

    def _build_screen_information_group(self) -> QGroupBox:
        group = QGroupBox("Screen information")
        form = QFormLayout(group)
        self._screen_info_fields: dict[str, QLabel] = {}
        for key, label in (
            ("monitor_id", "Screen ID"),
            ("resolution", "Resolution"),
            ("physical_size", "Physical size"),
            ("refresh_rate", "Refresh rate"),
        ):
            value = self._new_information_label()
            self._screen_info_fields[key] = value
            form.addRow(f"{label}:", value)
        return group

    def _build_monitor_information_group(self) -> QGroupBox:
        group = QGroupBox("Associated monitors (up to 3)")
        layout = QVBoxLayout(group)
        self._associated_monitor_labels: list[QLabel] = []
        for index in range(self._MAX_ASSOCIATED_MONITORS):
            label = QLabel(f"Monitor {index + 1}: no monitor information available")
            label.setFrameShape(QFrame.Shape.StyledPanel)
            label.setMinimumHeight(28)
            label.setMargin(6)
            self._associated_monitor_labels.append(label)
            layout.addWidget(label)
        return group

    def _build_session_information_group(self) -> QGroupBox:
        group = QGroupBox("SLM session")
        layout = QGridLayout(group)
        self._session_info_fields: dict[str, QLabel] = {}
        for index, (key, label) in enumerate(
            (
                ("heros_name", "Hero name"),
                ("status", "Status"),
                ("submitted_count", "Submitted"),
                ("accepted_count", "Accepted"),
                ("invalid_count", "Invalid"),
                ("displayed_count", "Displayed"),
                ("latest_revision", "Latest revision"),
                ("last_displayed_revision", "Displayed revision"),
            )
        ):
            row, column = divmod(index, 2)
            field = self._new_information_label()
            self._session_info_fields[key] = field
            layout.addWidget(QLabel(f"{label}:"), row, column * 2)
            layout.addWidget(field, row, column * 2 + 1)
        return group

    def _build_pattern_group(self) -> QGroupBox:
        group = QGroupBox("Pattern composition")
        layout = QHBoxLayout(group)
        layout.setSpacing(8)

        layout.addWidget(
            self._build_pattern_component(
                "Base aberration", component_key="base", has_file_selector=True
            ),
            1,
        )
        layout.addWidget(self._build_operator_label("+"))
        layout.addWidget(
            self._build_pattern_component("Hologram", component_key="hologram", has_file_selector=True),
            1,
        )
        layout.addWidget(self._build_operator_label("+"))
        layout.addWidget(
            self._build_pattern_component(
                "Modification", component_key="modification", has_shift_controls=True
            ),
            1,
        )
        layout.addWidget(self._build_operator_label("="))
        layout.addWidget(
            self._build_pattern_component("Total hologram", component_key="total", has_apply_button=True),
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
        has_apply_button: bool = False,
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
        preview.setFrameShape(QFrame.Shape.StyledPanel)
        preview.setFixedHeight(90)
        preview.setStyleSheet("background: #4a4a4a; color: #d0d0d0;")
        if component_key is not None:
            self._preview_labels[component_key] = preview
        layout.addWidget(preview)

        if has_apply_button:
            layout.addWidget(QPushButton("Apply pattern"))
            layout.addStretch()
            return component

        enabled = QCheckBox("Active")
        enabled.setChecked(True)
        layout.addWidget(enabled)

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

        if has_shift_controls:
            for axis in ("X", "Y", "Z"):
                layout.addLayout(self._build_shift_row(axis))

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

        monitor_id = self._selected_monitor_id()
        if monitor_id is None:
            self._write_console(f"Error importing {component_name}: no screen is selected")
            return
        self._loaded_patterns.setdefault(monitor_id, {})[component_key] = pattern
        self._loaded_pattern_paths.setdefault(monitor_id, {})[component_key] = file_path
        path_field = self._pattern_path_fields[component_key]
        path_field.setText(Path(file_path).name)
        path_field.setToolTip(file_path)
        self._write_console(
            f"Imported {component_name} from {Path(file_path).name} ({pattern.shape[1]}x{pattern.shape[0]})"
        )
        self._upload_pattern(component_key, component_name, pattern, monitor_id)

    def _upload_pattern(
        self,
        component_key: str,
        component_name: str,
        pattern: NDArray[np.float32],
        monitor_id: str,
    ) -> None:
        displayer = self._monitor_manager.ensure_displayer(monitor_id)
        if displayer is None:
            self._write_console(f"Error applying {component_name}: screen is no longer available")
            return
        if pattern.shape != displayer.shape:
            self._write_console(
                f"Warning: {component_name} size {pattern.shape} differs from SLM size "
                f"{displayer.shape}; attempting automatic resize."
            )

        try:
            if component_key == "base":
                displayer.setCorrectionPattern(pattern)
            else:
                displayer.setHologramPattern(pattern)
        except PatternSizeMismatchError as error:
            self._write_console(f"Error applying {component_name}: {error}")
            return
        except Exception as error:
            self._write_console(f"Error applying {component_name}: {error}")
            return

        self._write_console(f"Applied {component_name} to the SLM session.")
        self.updatePreview()

    def updatePreview(self) -> None:
        """Update the bounded grayscale previews for the selected screen's patterns."""
        monitor_id = self._selected_monitor_id()
        displayer = self._monitor_manager.get_displayer(monitor_id) if monitor_id else None
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
        for component_key, pattern in patterns.items():
            self._set_preview_image(self._preview_labels[component_key], pattern)

    @staticmethod
    def _set_preview_image(preview: QLabel, pattern: NDArray[np.float32]) -> None:
        image_bytes = phaseToByte(np.ascontiguousarray(pattern, dtype=np.float32))
        height, width = image_bytes.shape
        max_width = max(1, min(preview.width(), 240))
        max_height = max(1, min(preview.height(), 90))
        scale = min(max_width / width, max_height / height, 1.0)
        target_width = max(1, round(width * scale))
        target_height = max(1, round(height * scale))
        row_indices = np.linspace(0, height - 1, target_height, dtype=np.intp)
        column_indices = np.linspace(0, width - 1, target_width, dtype=np.intp)
        preview_bytes = np.ascontiguousarray(image_bytes[row_indices][:, column_indices])
        image = QImage(
            preview_bytes.data,
            target_width,
            target_height,
            preview_bytes.strides[0],
            QImage.Format.Format_Grayscale8,
        ).copy()
        preview.setPixmap(QPixmap.fromImage(image))

    def _write_console(self, message: str) -> None:
        self._console.append(message)

    def _build_shift_row(self, axis: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(4)
        axis_label = QLabel(axis)
        axis_label.setMinimumWidth(14)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(-100, 100)
        value_input = QLineEdit("0")
        value_input.setMaximumWidth(46)
        value_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(axis_label)
        row.addWidget(slider, 1)
        row.addWidget(value_input)
        return row

    def _build_console_group(self) -> QGroupBox:
        group = QGroupBox("Console")
        layout = QVBoxLayout(group)
        self._console = QTextEdit()
        self._console.setReadOnly(True)
        self._console.setPlaceholderText("Status messages will appear here.")
        self._console.setFixedHeight(78)
        layout.addWidget(self._console)
        return group

    @staticmethod
    def _new_information_label() -> QLabel:
        label = QLabel("—")
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        return label

    def _update_selected_screen(self, *_: object) -> None:
        monitor_id = self._selected_monitor_id()
        if monitor_id is None:
            self._content_stack.setCurrentWidget(self._empty_page)
            return

        views = {view.monitor_id: view for view in self._monitor_manager.iter_debug_views()}
        view = views.get(monitor_id)
        if view is None:
            self._content_stack.setCurrentWidget(self._empty_page)
            return

        self._content_stack.setCurrentWidget(self._details_page)
        self._screen_title.setText(view.screen_name or "Unnamed screen")
        status = SessionState.to_string(view.state)
        self._screen_status.setText(status)
        pattern_paths = self._loaded_pattern_paths.get(monitor_id, {})
        for component_key, path_field in self._pattern_path_fields.items():
            file_path = pattern_paths.get(component_key, "")
            path_field.setText(Path(file_path).name if file_path else "")
            path_field.setToolTip(file_path)
        for key, value in {
            "monitor_id": view.monitor_id,
            "resolution": view.resolution,
            "physical_size": view.physical_size,
            "refresh_rate": view.refresh_rate,
        }.items():
            self._screen_info_fields[key].setText(value)
        for key, value in {
            "heros_name": view.heros_name or "—",
            "status": status,
            "submitted_count": str(view.submitted_count),
            "accepted_count": str(view.accepted_count),
            "invalid_count": str(view.invalid_count),
            "displayed_count": str(view.displayed_count),
            "latest_revision": str(view.latest_revision),
            "last_displayed_revision": str(view.last_displayed_revision),
        }.items():
            self._session_info_fields[key].setText(value)
        self.updatePreview()

    def _selected_monitor_id(self) -> str | None:
        item = self._list_widget.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    @staticmethod
    def _build_item_label(view: SessionDebugView) -> str:
        return view.screen_name or view.monitor_id

    @staticmethod
    def _build_item_tooltip(view: SessionDebugView) -> str:
        return f"{view.resolution} | {SessionState.to_string(view.state)}"
