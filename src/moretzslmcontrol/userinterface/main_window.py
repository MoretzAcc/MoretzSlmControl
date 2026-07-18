"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from moretzslmcontrol.userinterface.models import SessionState

if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    from moretzslmcontrol.userinterface.monitor_manager import MonitorManager
    from moretzslmcontrol.userinterface.models import SessionDebugView


class MainWindow(QMainWindow):
    def __init__(self, monitor_manager: MonitorManager) -> None:
        super().__init__()
        self._monitor_manager = monitor_manager
        self._monitor_manager.recordsChanged.connect(self.refresh_views)

        self.setWindowTitle("SLM Display Control")
        self.resize(1100, 700)

        self._list_widget = QListWidget()
        self._details = QTextEdit()
        self._details.setReadOnly(True)

        self._refresh_button = QPushButton("Refresh")
        self._activate_button = QPushButton("Activate")
        self._deactivate_button = QPushButton("Deactivate")

        self._refresh_button.clicked.connect(self._monitor_manager.rescan_screens)
        self._activate_button.clicked.connect(self._activate_selected)
        self._deactivate_button.clicked.connect(self._deactivate_selected)
        self._list_widget.currentItemChanged.connect(self._update_details_panel)

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Detected monitors"))
        left_layout.addWidget(self._list_widget)

        button_row = QHBoxLayout()
        button_row.addWidget(self._refresh_button)
        button_row.addWidget(self._activate_button)
        button_row.addWidget(self._deactivate_button)
        left_layout.addLayout(button_row)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Details / debug data"))
        right_layout.addWidget(self._details)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.refresh_views()

    def refresh_views(self) -> None:
        selected_monitor_id = self._selected_monitor_id()
        self._list_widget.clear()
        for view in self._monitor_manager.iter_debug_views():
            item = QListWidgetItem(self._build_item_summary(view))
            item.setData(Qt.ItemDataRole.UserRole, view.monitor_id)
            self._list_widget.addItem(item)
            if view.monitor_id == selected_monitor_id:
                self._list_widget.setCurrentItem(item)
        if self._list_widget.currentItem() is None and self._list_widget.count() > 0:
            self._list_widget.setCurrentRow(0)
        self._update_details_panel()

    def _activate_selected(self) -> None:
        monitor_id = self._selected_monitor_id()
        if monitor_id is None:
            QMessageBox.information(self, "No selection", "Select a monitor first.")
            return
        self._monitor_manager.activate_monitor(monitor_id)

    def _deactivate_selected(self) -> None:
        monitor_id = self._selected_monitor_id()
        if monitor_id is None:
            QMessageBox.information(self, "No selection", "Select a monitor first.")
            return
        self._monitor_manager.deactivate_monitor(monitor_id)

    def _selected_monitor_id(self) -> str | None:
        item = self._list_widget.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _update_details_panel(self) -> None:
        monitor_id = self._selected_monitor_id()
        if monitor_id is None:
            self._details.clear()
            return
        views = {view.monitor_id: view for view in self._monitor_manager.iter_debug_views()}
        view = views.get(monitor_id)
        if view is None:
            self._details.clear()
            return
        self._details.setPlainText(self._build_detail_text(view))

    @staticmethod
    def _build_item_summary(view: SessionDebugView) -> str:
        status = SessionState.to_string(view.state)
        active = "Hero online" if view.ready_for_frames else "Hero offline"
        return f"{view.resolution} | {view.screen_name or 'no_name'} | {status} | {active}"

    @staticmethod
    def _build_detail_text(view: SessionDebugView) -> str:
        def header(text: str) -> str:
            return f"--- {text} ---"

        lines = [
            header("Session Details"),
            f"monitor_id: {view.monitor_id}",
            f"session_id: {view.session_id}",
            f"state: {view.state.value}",
            f"ready_for_frames: {view.ready_for_frames}",
            f"has_screen_attached: {view.has_screen_attached}",
            "",
            f"heros_name: {view.heros_name}",
            "",
            header("Monitor Parameters"),
            f"resolution: {view.resolution}",
            f"physical_size: {view.physical_size}",
            f"refresh_rate: {view.refresh_rate}",
            f"screen_name: {view.screen_name}",
            f"manufacturer: {view.manufacturer}",
            f"model: {view.model}",
            f"port_name: {view.port_name}",
            f"serial_number: {view.serial_number}",
            "",
            header("Hologram Statistics"),
            f"submitted_count: {view.submitted_count}",
            f"accepted_count: {view.accepted_count}",
            f"invalid_count: {view.invalid_count}",
            f"displayed_count: {view.displayed_count}",
            f"latest_revision: {view.latest_revision}",
            f"last_displayed_revision: {view.last_displayed_revision}",
        ]
        if view.last_error:
            lines.extend(["", f"last_error: {view.last_error}"])
        return "\n".join(lines)
