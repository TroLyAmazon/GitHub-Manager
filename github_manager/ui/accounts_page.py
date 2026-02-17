"""
Accounts page: list accounts, add account (PAT, validate, save to Credential Manager + accounts.json).
"""
import uuid
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QLabel,
    QMessageBox,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
import requests

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.store_json import read_json, write_json
from core.secrets import create_and_store_token, get_token, delete_token
from core.github_api import get_user


class CheckTokenWorker(QThread):
    """Check PAT via GET /user in background."""
    result = Signal(bool, str)  # valid, message

    def __init__(self, token: str, parent=None):
        super().__init__(parent)
        self.token = token

    def run(self):
        if not self.token:
            self.result.emit(False, "Không có token (đã xóa hoặc mất).")
            return
        user = get_user(self.token)
        if user:
            self.result.emit(True, f"PAT còn hạn. Login: {user.get('login', '')}")
        else:
            self.result.emit(False, "PAT hết hạn hoặc không hợp lệ.")


def _accounts_data() -> dict:
    return read_json("accounts.json")


def _ensure_accounts_list(data: dict) -> list:
    if "accounts" not in data:
        data["accounts"] = []
    return data["accounts"]


class AddAccountDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add GitHub Account")
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("e.g. My Personal")
        form.addRow("Label:", self.label_edit)

        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_edit.setPlaceholderText("Fine-grained PAT (no username/password)")
        form.addRow("PAT Token:", self.token_edit)

        layout.addLayout(form)

        self.validate_btn = QPushButton("Validate")
        self.validate_btn.clicked.connect(self._validate)
        layout.addWidget(self.validate_btn)

        self.preview = QLabel()
        self.preview.setMinimumHeight(60)
        self.preview.setStyleSheet("padding: 8px; background: #1e1e1e; border-radius: 4px;")
        self.preview.setText("Validate to see login and avatar.")
        layout.addWidget(self.preview)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(48, 48)
        self.avatar_label.setVisible(False)
        layout.addWidget(self.avatar_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._user_data = None

    def _validate(self):
        token = self.token_edit.text().strip()
        if not token:
            QMessageBox.warning(self, "Validation", "Enter a PAT token.")
            return
        self.validate_btn.setEnabled(False)
        self.validate_btn.setText("Validating...")
        try:
            user = get_user(token)
            if user:
                self._user_data = user
                login = user.get("login", "")
                avatar_url = user.get("avatar_url", "")
                self.preview.setText(f"Login: {login}")
                if avatar_url:
                    try:
                        r = requests.get(avatar_url, timeout=5)
                        if r.status_code == 200:
                            px = QPixmap()
                            px.loadFromData(r.content)
                            if not px.isNull():
                                self.avatar_label.setPixmap(px.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                                self.avatar_label.setVisible(True)
                    except Exception:
                        pass
                QMessageBox.information(self, "Validation", "Token is valid.")
            else:
                self._user_data = None
                self.avatar_label.setVisible(False)
                self.preview.setText("Validate to see login and avatar.")
                QMessageBox.warning(self, "Validation", "Invalid token or network error.")
        finally:
            self.validate_btn.setEnabled(True)
            self.validate_btn.setText("Validate")

    def _accept_if_valid(self):
        label = self.label_edit.text().strip()
        if not label:
            QMessageBox.warning(self, "Add Account", "Enter a label.")
            return
        token = self.token_edit.text().strip()
        if not token:
            QMessageBox.warning(self, "Add Account", "Enter a PAT token.")
            return
        if not self._user_data:
            QMessageBox.warning(self, "Add Account", "Validate the token first.")
            return
        self.accept()

    def get_label(self):
        return self.label_edit.text().strip()

    def get_token(self):
        return self.token_edit.text().strip()

    def get_user_data(self):
        return self._user_data


class AccountsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addStretch()
        self.check_btn = QPushButton("Check token (PAT còn hạn?)")
        self.check_btn.clicked.connect(self._check_token)
        top.addWidget(self.check_btn)
        self.delete_btn = QPushButton("Delete account")
        self.delete_btn.clicked.connect(self._delete_account)
        top.addWidget(self.delete_btn)
        add_btn = QPushButton("Add Account")
        add_btn.clicked.connect(self._add_account)
        top.addWidget(add_btn)
        layout.addLayout(top)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.list_widget)

        self._refresh_list()

    def _refresh_list(self):
        self.list_widget.clear()
        data = _accounts_data()
        for acc in _ensure_accounts_list(data):
            label = acc.get("label", "?")
            login = acc.get("login", "")
            item = QListWidgetItem(f"{label}  —  {login}")
            item.setData(Qt.ItemDataRole.UserRole, acc)
            self.list_widget.addItem(item)

    def _add_account(self):
        dlg = AddAccountDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        label = dlg.get_label()
        token = dlg.get_token()
        user = dlg.get_user_data()
        secret_key = create_and_store_token(token)
        account_id = str(uuid.uuid4())
        data = _accounts_data()
        accounts = _ensure_accounts_list(data)
        accounts.append({
            "id": account_id,
            "label": label,
            "secretKey": secret_key,
            "login": user.get("login", ""),
            "avatarUrl": user.get("avatar_url", ""),
        })
        data["accounts"] = accounts
        write_json("accounts.json", data)
        self._refresh_list()
        QMessageBox.information(self, "Accounts", "Account added and token stored securely.")

    def _get_selected_account(self):
        item = self.list_widget.currentItem()
        if not item:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _check_token(self):
        acc = self._get_selected_account()
        if not acc:
            QMessageBox.warning(self, "Accounts", "Chọn một tài khoản trong danh sách.")
            return
        token = get_token(acc.get("secretKey", ""))
        self.check_btn.setEnabled(False)
        self.check_btn.setText("Đang kiểm tra...")
        self._check_worker = CheckTokenWorker(token, self)
        self._check_worker.result.connect(self._on_check_done)
        self._check_worker.finished.connect(self._check_worker.deleteLater)
        self._check_worker.start()

    def _on_check_done(self, valid: bool, message: str):
        self.check_btn.setEnabled(True)
        self.check_btn.setText("Check token (PAT còn hạn?)")
        if valid:
            QMessageBox.information(self, "Check token", message)
        else:
            QMessageBox.warning(self, "Check token", message)

    def _delete_account(self):
        acc = self._get_selected_account()
        if not acc:
            QMessageBox.warning(self, "Accounts", "Chọn một tài khoản để xóa.")
            return
        label = acc.get("label", "?")
        login = acc.get("login", "")
        reply = QMessageBox.question(
            self,
            "Delete account",
            f"Xóa tài khoản \"{label}\" ({login})?\nToken sẽ bị xóa khỏi Windows Credential Manager.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        account_id = acc.get("id", "")
        secret_key = acc.get("secretKey", "")
        delete_token(secret_key)
        data = _accounts_data()
        accounts = _ensure_accounts_list(data)
        data["accounts"] = [a for a in accounts if a.get("id") != account_id]
        write_json("accounts.json", data)
        self._refresh_list()
        QMessageBox.information(self, "Accounts", "Đã xóa tài khoản và token.")

    def get_accounts(self):
        data = _accounts_data()
        return _ensure_accounts_list(data)
