"""
Accounts page: list accounts, add account (PAT, validate, save to Credential Manager + accounts.json).
"""
import uuid
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QLabel,
    QMessageBox,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QIcon, QPainter, QColor, QPen, QBrush
import requests

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.store_json import read_json, write_json
from core.secrets import create_and_store_token, get_token, delete_token
from core.github_api import get_user, get_user_emails


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


class CheckAllPatWorker(QThread):
    """Check PAT for many accounts; emit (account_id, valid) for each."""
    result_one = Signal(str, bool)  # account_id, valid

    def __init__(self, accounts: list, parent=None):
        super().__init__(parent)
        self.accounts = accounts

    def run(self):
        now = datetime.utcnow().isoformat() + "Z"
        for acc in self.accounts:
            aid = acc.get("id", "")
            token = get_token(acc.get("secretKey", ""))
            valid = get_user(token) is not None
            self.result_one.emit(aid, valid)


def _accounts_data() -> dict:
    return read_json("accounts.json")


def _ensure_accounts_list(data: dict) -> list:
    if "accounts" not in data:
        data["accounts"] = []
    return data["accounts"]


def _format_display_date(iso_str: str) -> str:
    """Format ISO date for display (e.g. 2025-02-17 15:30). Trả về rỗng nếu không có."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso_str


def _status_icon_and_text(pat_status: str) -> tuple[QIcon | None, str]:
    """Trả về (icon, text) cho cột PAT Status: LIVE / Chưa Check / Dead."""
    size = 22
    if pat_status == "Valid":
        # Tích xanh phát sáng + LIVE
        px = QPixmap(size, size)
        px.fill(Qt.GlobalColor.transparent)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#00dd66"))
        p.drawEllipse(2, 2, size - 4, size - 4)
        p.setPen(QPen(QColor("#ffffff"), 2.5))
        p.drawLine(6, 11, 10, 15)
        p.drawLine(10, 15, 18, 7)
        p.end()
        return QIcon(px), "LIVE"
    if pat_status == "Invalid":
        # Dấu X đỏ phát sáng + Dead
        px = QPixmap(size, size)
        px.fill(Qt.GlobalColor.transparent)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#ff4444"))
        p.drawEllipse(2, 2, size - 4, size - 4)
        p.setPen(QPen(QColor("#ffffff"), 2.5))
        p.drawLine(6, 6, 16, 16)
        p.drawLine(16, 6, 6, 16)
        p.end()
        return QIcon(px), "Dead"
    # Chưa check: nút tròn xám + Chưa Check
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#888888"))
    p.drawEllipse(2, 2, size - 4, size - 4)
    p.end()
    return QIcon(px), "Chưa Check"


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

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Tên hiển thị khi commit (contributor name)")
        form.addRow("Contributor name:", self.name_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Email dùng cho commit (phải trùng tài khoản GitHub để tính contributions)")
        form.addRow("Contributor email:", self.email_edit)

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
                # Điền sẵn contributor name và email (có thể sửa trước khi Save)
                self.name_edit.setText(user.get("name") or login)
                email = user.get("email")
                if not email:
                    emails = get_user_emails(token)
                    if emails:
                        primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
                        if primary:
                            email = primary.get("email", "")
                    if not email:
                        email = f"{login}@users.noreply.github.com"
                self.email_edit.setText(email)
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
            QMessageBox.warning(self, "Add Account", "Nhập Label.")
            return
        token = self.token_edit.text().strip()
        if not token:
            QMessageBox.warning(self, "Add Account", "Nhập PAT token.")
            return
        if not self._user_data:
            QMessageBox.warning(self, "Add Account", "Bấm Validate token trước.")
            return
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Add Account", "Nhập Contributor name (tên hiển thị khi commit).")
            return
        email = self.email_edit.text().strip()
        if not email:
            QMessageBox.warning(self, "Add Account", "Nhập Contributor email (để GitHub tính contributions đúng tài khoản).")
            return
        self.accept()

    def get_label(self):
        return self.label_edit.text().strip()

    def get_token(self):
        return self.token_edit.text().strip()

    def get_contributor_name(self):
        return self.name_edit.text().strip()

    def get_contributor_email(self):
        return self.email_edit.text().strip()

    def get_user_data(self):
        return self._user_data


class EditAccountDialog(QDialog):
    """Sửa Label, Contributor name, email (không đổi PAT)."""
    def __init__(self, account: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Account")
        self.account = account
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.label_edit = QLineEdit()
        self.label_edit.setText(account.get("label", ""))
        form.addRow("Label:", self.label_edit)
        self.name_edit = QLineEdit()
        self.name_edit.setText(account.get("name", ""))
        form.addRow("Contributor name:", self.name_edit)
        self.email_edit = QLineEdit()
        self.email_edit.setText(account.get("email", ""))
        form.addRow("Contributor email:", self.email_edit)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _accept(self):
        if not self.label_edit.text().strip():
            QMessageBox.warning(self, "Edit", "Nhập Label.")
            return
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Edit", "Nhập Contributor name.")
            return
        if not self.email_edit.text().strip():
            QMessageBox.warning(self, "Edit", "Nhập Contributor email.")
            return
        self.accept()

    def get_label(self):
        return self.label_edit.text().strip()

    def get_contributor_name(self):
        return self.name_edit.text().strip()

    def get_contributor_email(self):
        return self.email_edit.text().strip()


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
        self.check_all_btn = QPushButton("Check ALL PAT")
        self.check_all_btn.clicked.connect(self._check_all_pat)
        top.addWidget(self.check_all_btn)
        self.edit_btn = QPushButton("✎ Edit")
        self.edit_btn.clicked.connect(self._edit_account)
        top.addWidget(self.edit_btn)
        self.delete_btn = QPushButton("Delete account")
        self.delete_btn.clicked.connect(self._delete_account)
        top.addWidget(self.delete_btn)
        add_btn = QPushButton("Add Account")
        add_btn.clicked.connect(self._add_account)
        top.addWidget(add_btn)
        layout.addLayout(top)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "Label", "Login", "PAT Status", "Last check",
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.table)

        self._refresh_list()

    def _refresh_list(self):
        data = _accounts_data()
        accounts = _ensure_accounts_list(data)
        self.table.setRowCount(len(accounts))
        for row, acc in enumerate(accounts):
            self.table.setItem(row, 0, QTableWidgetItem(acc.get("label", "?")))
            self.table.setItem(row, 1, QTableWidgetItem(acc.get("login", "")))
            status_icon, status_text = _status_icon_and_text(acc.get("patStatus", ""))
            status_item = QTableWidgetItem(status_text)
            if status_icon:
                status_item.setIcon(status_icon)
            self.table.setItem(row, 2, status_item)
            self.table.setItem(row, 3, QTableWidgetItem(_format_display_date(acc.get("lastCheckAt", ""))))
            for col in range(4):
                item = self.table.item(row, col)
                if item:
                    item.setData(Qt.ItemDataRole.UserRole, acc)
        self.table.resizeColumnsToContents()

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
        login = user.get("login", "")
        # Name và email do user nhập trong dialog (contributor cho commit)
        name = dlg.get_contributor_name()
        email = dlg.get_contributor_email()

        added_at = datetime.utcnow().isoformat() + "Z"
        accounts.append({
            "id": account_id,
            "label": label,
            "secretKey": secret_key,
            "login": login,
            "email": email,
            "name": name,
            "avatarUrl": user.get("avatar_url", ""),
            "addedAt": added_at,
            "patStatus": "Chưa check",
            "lastCheckAt": "",
        })
        data["accounts"] = accounts
        write_json("accounts.json", data)
        self._refresh_list()
        QMessageBox.information(self, "Accounts", "Account added and token stored securely.")

    def _get_selected_account(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

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
        acc = self._get_selected_account()
        if acc:
            data = _accounts_data()
            accounts = _ensure_accounts_list(data)
            now = datetime.utcnow().isoformat() + "Z"
            status = "Valid" if valid else "Invalid"
            for a in accounts:
                if a.get("id") == acc.get("id"):
                    a["lastCheckAt"] = now
                    a["patStatus"] = status
                    break
            write_json("accounts.json", data)
            self._refresh_list()
        if valid:
            QMessageBox.information(self, "Check token", message)
        else:
            QMessageBox.warning(self, "Check token", message)

    def _check_all_pat(self):
        accounts = _ensure_accounts_list(_accounts_data())
        if not accounts:
            QMessageBox.warning(self, "Accounts", "Chưa có tài khoản nào.")
            return
        self.check_btn.setEnabled(False)
        self.check_all_btn.setEnabled(False)
        self.check_all_btn.setText("Đang check...")
        self._check_all_data = _accounts_data()
        self._check_all_accounts = _ensure_accounts_list(self._check_all_data)
        self._check_all_now = datetime.utcnow().isoformat() + "Z"
        self._check_all_worker = CheckAllPatWorker(self._check_all_accounts, self)
        self._check_all_worker.result_one.connect(self._on_check_all_one)
        self._check_all_worker.finished.connect(self._on_check_all_finished)
        self._check_all_worker.start()

    def _on_check_all_one(self, account_id: str, valid: bool):
        for a in self._check_all_accounts:
            if a.get("id") == account_id:
                a["patStatus"] = "Valid" if valid else "Invalid"
                a["lastCheckAt"] = self._check_all_now
                break

    def _on_check_all_finished(self):
        write_json("accounts.json", self._check_all_data)
        self._refresh_list()
        self.check_btn.setEnabled(True)
        self.check_all_btn.setEnabled(True)
        self.check_all_btn.setText("Check ALL PAT")
        self._check_all_worker.deleteLater()
        QMessageBox.information(self, "Check ALL PAT", "Đã kiểm tra xong tất cả tài khoản.")

    def _edit_account(self):
        acc = self._get_selected_account()
        if not acc:
            QMessageBox.warning(self, "Accounts", "Chọn một tài khoản để sửa.")
            return
        dlg = EditAccountDialog(acc, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = _accounts_data()
        accounts = _ensure_accounts_list(data)
        for a in accounts:
            if a.get("id") == acc.get("id"):
                a["label"] = dlg.get_label()
                a["name"] = dlg.get_contributor_name()
                a["email"] = dlg.get_contributor_email()
                break
        write_json("accounts.json", data)
        self._refresh_list()
        QMessageBox.information(self, "Edit", "Đã lưu thay đổi.")

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
