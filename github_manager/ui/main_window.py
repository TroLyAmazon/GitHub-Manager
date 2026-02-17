"""
Main window with sidebar navigation: Accounts, Repositories, Commit & Push, Runs / Logs.
"""
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from .accounts_page import AccountsPage
from .repos_page import ReposPage
from .commit_page import CommitPage
from .runs_page import RunsPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GitHub Manager")
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(200)
        self.sidebar.setFont(QFont("Segoe UI", 10))
        for label, key in [
            ("Accounts", "accounts"),
            ("Repositories", "repos"),
            ("Commit & Push", "commit"),
            ("Runs / Logs", "runs"),
        ]:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.sidebar.addItem(item)
        self.sidebar.setCurrentRow(0)
        self.sidebar.currentRowChanged.connect(self._on_page_changed)

        # Stacked pages
        self.stack = QStackedWidget()
        self.accounts_page = AccountsPage(self)
        self.repos_page = ReposPage(self)
        self.commit_page = CommitPage(self)
        self.runs_page = RunsPage(self)

        self.stack.addWidget(self.accounts_page)
        self.stack.addWidget(self.repos_page)
        self.stack.addWidget(self.commit_page)
        self.stack.addWidget(self.runs_page)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)

        # Style sidebar
        self.sidebar.setFrameShape(QFrame.Shape.NoFrame)
        self.sidebar.setStyleSheet("""
            #sidebar {
                background-color: #2d2d30;
                color: #cccccc;
                padding: 8px 0;
            }
            #sidebar::item {
                padding: 12px 16px;
                border-radius: 4px;
            }
            #sidebar::item:selected {
                background-color: #094771;
                color: #ffffff;
            }
            #sidebar::item:hover:!selected {
                background-color: #3d3d40;
            }
        """)

    def _on_page_changed(self, row: int):
        if row >= 0:
            self.stack.setCurrentIndex(row)
            if row == 1:
                self.repos_page.refresh_accounts()
            elif row == 2:
                self.commit_page.refresh_accounts()
            elif row == 3:
                self.runs_page.refresh_runs()

    def get_accounts(self):
        """Return list of account dicts from accounts page / storage."""
        return self.accounts_page.get_accounts()
