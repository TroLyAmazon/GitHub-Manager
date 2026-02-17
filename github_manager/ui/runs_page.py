"""
Runs / Logs page: list run entries from runs.json, show log path and status.
"""
import os
import sys
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QLabel,
)
from PySide6.QtCore import Qt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.store_json import read_json, get_logs_dir


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
        row.addStretch()
        layout.addLayout(row)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Repo", "Branch", "File", "Status", "Commit SHA", "Log"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.refresh_runs()

    def refresh_runs(self):
        runs = read_json("runs.json")
        if not isinstance(runs, list):
            runs = []
        self.table.setRowCount(len(runs))
        for row, r in enumerate(reversed(runs)):
            self.table.setItem(row, 0, QTableWidgetItem(r.get("repoFullName", "")))
            self.table.setItem(row, 1, QTableWidgetItem(r.get("branch", "")))
            self.table.setItem(row, 2, QTableWidgetItem(r.get("fileName", "")))
            self.table.setItem(row, 3, QTableWidgetItem(r.get("status", "")))
            self.table.setItem(row, 4, QTableWidgetItem(r.get("commitSha", "")[:8] if r.get("commitSha") else ""))
            log_path = r.get("logPath", "")
            self.table.setItem(row, 5, QTableWidgetItem(log_path))
        self.table.resizeColumnsToContents()
