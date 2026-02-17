"""
Runs / Logs page: list run entries from runs.json, read-only, Delete / Delete All.
"""
import os
import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QPushButton,
    QLabel,
    QMessageBox,
)
from PySide6.QtCore import Qt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.store_json import read_json, write_json, get_logs_dir


def _format_time(iso_str: str) -> str:
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso_str


class RunsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        row.addWidget(QLabel("Run history (runs.json)"))
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_runs)
        row.addWidget(refresh_btn)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_selected)
        row.addWidget(delete_btn)
        delete_all_btn = QPushButton("Delete All")
        delete_all_btn.clicked.connect(self._delete_all)
        row.addWidget(delete_all_btn)
        row.addStretch()
        layout.addLayout(row)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Time", "Repo", "Branch", "File", "Status", "Commit SHA", "Log"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        self.refresh_runs()

    def refresh_runs(self):
        runs = read_json("runs.json")
        if not isinstance(runs, list):
            runs = []
        self.table.setRowCount(len(runs))
        for row, r in enumerate(reversed(runs)):
            time_str = _format_time(r.get("startTime", ""))
            self.table.setItem(row, 0, QTableWidgetItem(time_str))
            self.table.setItem(row, 1, QTableWidgetItem(r.get("repoFullName", "")))
            self.table.setItem(row, 2, QTableWidgetItem(r.get("branch", "")))
            self.table.setItem(row, 3, QTableWidgetItem(r.get("fileName", "")))
            self.table.setItem(row, 4, QTableWidgetItem(r.get("status", "")))
            self.table.setItem(row, 5, QTableWidgetItem(r.get("commitSha", "")[:8] if r.get("commitSha") else ""))
            self.table.setItem(row, 6, QTableWidgetItem(r.get("logPath", "")))
            for col in range(7):
                item = self.table.item(row, col)
                if item:
                    item.setData(Qt.ItemDataRole.UserRole, r)
        self.table.resizeColumnsToContents()

    def _get_selected_runs(self):
        """Return list of run dicts for selected rows (each run is stored in row)."""
        rows = set(self.table.selectedIndexes())
        run_rows = set()
        for idx in rows:
            run_rows.add(idx.row())
        runs = []
        seen = set()
        for row in run_rows:
            item = self.table.item(row, 0)
            if item:
                r = item.data(Qt.ItemDataRole.UserRole)
                if r is not None and id(r) not in seen:
                    seen.add(id(r))
                    runs.append(r)
        return runs

    def _run_key(self, r):
        return (r.get("startTime"), r.get("repoFullName"), r.get("fileName"), r.get("branch"))

    def _delete_selected(self):
        selected = self._get_selected_runs()
        if not selected:
            QMessageBox.warning(self, "Runs", "Chọn ít nhất một dòng để xóa.")
            return
        reply = QMessageBox.question(
            self, "Delete",
            f"Xóa {len(selected)} mục đã chọn?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        runs = read_json("runs.json")
        if not isinstance(runs, list):
            runs = []
        keys_to_remove = {self._run_key(r) for r in selected}
        runs = [r for r in runs if self._run_key(r) not in keys_to_remove]
        write_json("runs.json", runs)
        self.refresh_runs()
        QMessageBox.information(self, "Runs", "Đã xóa.")

    def _delete_all(self):
        runs = read_json("runs.json")
        if not isinstance(runs, list) or len(runs) == 0:
            QMessageBox.information(self, "Runs", "Không có dữ liệu.")
            return
        reply = QMessageBox.question(
            self, "Delete All",
            "Xóa toàn bộ lịch sử runs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        write_json("runs.json", [])
        self.refresh_runs()
        QMessageBox.information(self, "Runs", "Đã xóa hết.")
