"""
Repositories page: select account, load repos (full name, private/public, default branch).
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
)
from PySide6.QtCore import Qt, QThread, Signal

from core.secrets import get_token
from core.github_api import get_repos


class LoadReposWorker(QThread):
    result = Signal(object)  # list of repo dicts or None

    def __init__(self, token: str, parent=None):
        super().__init__(parent)
        self.token = token

    def run(self):
        repos = get_repos(self.token) if self.token else None
        self.result.emit(repos)


class ReposPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        row.addWidget(QLabel("Account:"))
        self.account_combo = QComboBox()
        self.account_combo.setMinimumWidth(220)
        row.addWidget(self.account_combo)
        self.load_btn = QPushButton("Load Repositories")
        self.load_btn.clicked.connect(self._load_repos)
        row.addWidget(self.load_btn)
        row.addStretch()
        layout.addLayout(row)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Full name", "Visibility", "Default branch", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.refresh_accounts()

    def refresh_accounts(self):
        self.account_combo.clear()
        for acc in self.main_window.get_accounts():
            self.account_combo.addItem(
                f"{acc.get('label', '?')} ({acc.get('login', '')})",
                acc,
            )

    def _load_repos(self):
        idx = self.account_combo.currentIndex()
        if idx < 0:
            return
        acc = self.account_combo.currentData()
        if not acc:
            return
        token = get_token(acc.get("secretKey", ""))
        if not token:
            self.table.setRowCount(0)
            return
        self.load_btn.setEnabled(False)
        self.load_btn.setText("Loading...")
        try:
            repos = get_repos(token)
            self.table.setRowCount(0)
            if repos:
                for r in repos:
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    full = r.get("full_name", "")
                    self.table.setItem(row, 0, QTableWidgetItem(full))
                    vis = "Private" if r.get("private") else "Public"
                    self.table.setItem(row, 1, QTableWidgetItem(vis))
                    self.table.setItem(row, 2, QTableWidgetItem(r.get("default_branch", "main")))
                    self.table.setItem(row, 3, QTableWidgetItem(""))
        finally:
            self.load_btn.setEnabled(True)
            self.load_btn.setText("Load Repositories")
