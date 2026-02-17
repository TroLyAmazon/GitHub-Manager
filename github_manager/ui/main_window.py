"""
Main window with sidebar navigation: Accounts, Repositories, Commit & Push, Runs / Logs.
"""
import os
import sys
import webbrowser
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QFrame,
    QMenuBar,
    QMenu,
    QDialog,
    QLabel,
    QPushButton,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon, QAction

from .accounts_page import AccountsPage
from .repos_page import ReposPage
from .commit_page import CommitPage
from .runs_page import RunsPage


def _app_root():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _icon_path():
    return os.path.join(_app_root(), "assets", "icon.ico")


class AboutDialog(QDialog):
    def __init__(self, version: str, github_url: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About GitHub Manager")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>GitHub Manager</h2>"))
        layout.addWidget(QLabel(f"Phiên bản / Version: <b>{version}</b>"))
        layout.addWidget(QLabel("<br/>"))
        link_label = QLabel(f'Project: <a href="{github_url}">{github_url}</a>')
        link_label.setOpenExternalLinks(True)
        layout.addWidget(link_label)
        open_btn = QPushButton("Mở link GitHub / Open GitHub")
        open_btn.clicked.connect(lambda: webbrowser.open(github_url))
        layout.addWidget(open_btn)
        close_btn = QPushButton("Đóng")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            from version import __version__, GITHUB_URL
        except ImportError:
            __version__ = "?.?.?"
            GITHUB_URL = "https://github.com/TroLyAmazon/GitHub-Manager"
        self._version = __version__
        self._github_url = GITHUB_URL
        self.setWindowTitle(f"GitHub Manager  v{__version__}")
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)
        if os.path.isfile(_icon_path()):
            self.setWindowIcon(QIcon(_icon_path()))

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

        # Menu: Help -> About
        menubar = self.menuBar()
        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About GitHub Manager", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

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

    def _show_about(self):
        AboutDialog(self._version, self._github_url, self).exec()

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
