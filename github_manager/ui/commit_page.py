"""
Commit & Push page: select account, repo, branch, multiple files; preview uploads/<filename>; run pipeline (one commit + push per file).
"""
import os
import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFileDialog,
    QMessageBox,
    QProgressBar,
)
from PySide6.QtCore import Qt, QThread, Signal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.store_json import (
    read_json,
    write_json,
    get_workspace_path,
    get_logs_dir,
)
from core.secrets import get_token
from core.github_api import get_repos
from core.path_policy import clean_filename, resolve_upload_path, ensure_upload_dir
from core.git_ops import clone_repo, checkout_branch, add_commit_push


def _runs_data() -> list:
    return read_json("runs.json")


def _append_run(entry: dict) -> None:
    data = _runs_data()
    data.append(entry)
    write_json("runs.json", data)


class CommitWorker(QThread):
    progress = Signal(int, int, str)  # current, total, message
    finished_signal = Signal()

    def __init__(self, account, repo_full_name, branch, file_paths, clone_url, parent=None):
        super().__init__(parent)
        self.account = account
        self.repo_full_name = repo_full_name
        self.branch = branch
        self.file_paths = file_paths
        self.clone_url = clone_url

    def run(self):
        account_id = self.account.get("id", "")
        token = get_token(self.account.get("secretKey", ""))
        if not token:
            self.progress.emit(0, len(self.file_paths), "No token for account")
            self.finished_signal.emit()
            return
        workspace = get_workspace_path(account_id, self.repo_full_name)
        owner_repo_dir = self.repo_full_name.replace("/", "_")
        # Clone if needed
        ok, msg = clone_repo(self.clone_url, token, workspace)
        if not ok:
            self.progress.emit(0, len(self.file_paths), f"Clone failed: {msg}")
            self.finished_signal.emit()
            return
        if self.branch:
            ok, _ = checkout_branch(workspace, self.branch)
            if not ok:
                checkout_branch(workspace, "main")
        uploads_dir = ensure_upload_dir(workspace)
        existing = set()
        for p in os.listdir(uploads_dir):
            if os.path.isfile(os.path.join(uploads_dir, p)):
                existing.add(p)
        total = len(self.file_paths)
        for i, src in enumerate(self.file_paths):
            filename = clean_filename(os.path.basename(src))
            dest_abs, rel_path = resolve_upload_path(uploads_dir, filename, existing)
            start_time = datetime.utcnow().isoformat() + "Z"
            log_dir = get_logs_dir()
            log_name = f"commit_{account_id}_{owner_repo_dir}_{i}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"
            log_path = os.path.join(log_dir, log_name)
            run_entry = {
                "accountId": account_id,
                "repoFullName": self.repo_full_name,
                "branch": self.branch or "default",
                "fileName": os.path.basename(src),
                "commitSha": "",
                "status": "Failed",
                "startTime": start_time,
                "endTime": "",
                "logPath": log_path,
            }
            lines = []
            try:
                import shutil
                shutil.copy2(src, dest_abs)
                commit_msg = f"Upload {os.path.basename(dest_abs)}"
                ok, commit_sha, err = add_commit_push(
                    workspace,
                    rel_path,
                    commit_msg,
                    token,
                    branch=self.branch or None,
                )
                end_time = datetime.utcnow().isoformat() + "Z"
                run_entry["endTime"] = end_time
                run_entry["commitSha"] = commit_sha or ""
                run_entry["status"] = "Success" if ok else "Failed"
                lines.append(f"File: {src}")
                lines.append(f"Dest: {rel_path}")
                lines.append(f"Commit: {commit_msg}")
                lines.append(f"Push: {'OK' if ok else err}")
            except Exception as e:
                run_entry["status"] = "Failed"
                run_entry["endTime"] = datetime.utcnow().isoformat() + "Z"
                lines.append(str(e))
            try:
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))
            except Exception:
                pass
            _append_run(run_entry)
            self.progress.emit(i + 1, total, run_entry["status"])
        self.finished_signal.emit()


class CommitPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._clone_url_map = {}  # repo_full_name -> clone_url for current account
        layout = QVBoxLayout(self)

        # Account
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("Account:"))
        self.account_combo = QComboBox()
        self.account_combo.setMinimumWidth(220)
        self.account_combo.currentIndexChanged.connect(self._on_account_changed)
        r1.addWidget(self.account_combo)
        r1.addStretch()
        layout.addLayout(r1)

        # Repo (we need repo list for this account; reuse API)
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("Repository:"))
        self.repo_combo = QComboBox()
        self.repo_combo.setMinimumWidth(280)
        self.repo_combo.currentIndexChanged.connect(self._on_repo_changed)
        r2.addWidget(self.repo_combo)
        load_repos_btn = QPushButton("Load repos")
        load_repos_btn.clicked.connect(self._load_repos_for_commit)
        r2.addWidget(load_repos_btn)
        r2.addStretch()
        layout.addLayout(r2)

        # Branch
        r3 = QHBoxLayout()
        r3.addWidget(QLabel("Branch:"))
        self.branch_combo = QComboBox()
        self.branch_combo.setMinimumWidth(180)
        r3.addWidget(self.branch_combo)
        r3.addStretch()
        layout.addLayout(r3)

        # Files
        r4 = QHBoxLayout()
        r4.addWidget(QLabel("Files:"))
        self.add_files_btn = QPushButton("Select files...")
        self.add_files_btn.clicked.connect(self._select_files)
        r4.addWidget(self.add_files_btn)
        r4.addStretch()
        layout.addLayout(r4)

        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(120)
        layout.addWidget(self.files_list)

        # Preview table: source -> uploads/<filename>
        layout.addWidget(QLabel("Preview (source → uploads/<filename>):"))
        self.preview_table = QTableWidget(0, 2)
        self.preview_table.setHorizontalHeaderLabels(["Source file", "uploads/..."])
        self.preview_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.preview_table)

        self.run_btn = QPushButton("Commit & Push (one commit per file)")
        self.run_btn.clicked.connect(self._run_commit_push)
        layout.addWidget(self.run_btn)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self._worker = None
        self.refresh_accounts()

    def refresh_accounts(self):
        self.account_combo.clear()
        for acc in self.main_window.get_accounts():
            self.account_combo.addItem(
                f"{acc.get('label', '?')} ({acc.get('login', '')})",
                acc,
            )
        self._clone_url_map.clear()
        self.repo_combo.clear()
        self.branch_combo.clear()

    def _on_account_changed(self):
        self._clone_url_map.clear()
        self.repo_combo.clear()
        self.branch_combo.clear()

    def _load_repos_for_commit(self):
        acc = self.account_combo.currentData()
        if not acc:
            return
        token = get_token(acc.get("secretKey", ""))
        if not token:
            QMessageBox.warning(self, "Commit", "No token for this account.")
            return
        repos = get_repos(token)
        self.repo_combo.clear()
        self._clone_url_map.clear()
        if repos:
            for r in repos:
                full = r.get("full_name", "")
                clone_url = r.get("clone_url", "")
                self.repo_combo.addItem(full, r)
                self._clone_url_map[full] = clone_url
        self._on_repo_changed()

    def _on_repo_changed(self):
        self.branch_combo.clear()
        repo = self.repo_combo.currentData()
        if repo:
            default = repo.get("default_branch", "main")
            self.branch_combo.addItem(default, default)
        acc = self.account_combo.currentData()
        if not acc:
            return
        workspace = get_workspace_path(acc.get("id", ""), self.repo_combo.currentText() or "")
        if os.path.isdir(workspace) and os.path.isdir(os.path.join(workspace, ".git")):
            from core.git_ops import get_branches
            for b in get_branches(workspace):
                if self.branch_combo.findText(b) < 0:
                    self.branch_combo.addItem(b, b)

    def _select_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select files to upload", "", "All files (*)")
        for p in paths:
            if p and self.files_list.findItems(p, Qt.MatchFlag.MatchExactly) == []:
                self.files_list.addItem(p)
        self._update_preview()

    def _update_preview(self):
        from core.path_policy import UPLOADS_BASE
        paths = [self.files_list.item(i).text() for i in range(self.files_list.count())]
        uploads_dir = ""
        existing = set()
        self.preview_table.setRowCount(len(paths))
        for row, src in enumerate(paths):
            name = clean_filename(os.path.basename(src))
            _, rel_path = resolve_upload_path(uploads_dir or "/", name, existing)
            self.preview_table.setItem(row, 0, QTableWidgetItem(src))
            self.preview_table.setItem(row, 1, QTableWidgetItem(rel_path))

    def _run_commit_push(self):
        acc = self.account_combo.currentData()
        if not acc:
            QMessageBox.warning(self, "Commit", "Select an account.")
            return
        repo_name = self.repo_combo.currentText()
        if not repo_name:
            QMessageBox.warning(self, "Commit", "Select a repository (Load repos first).")
            return
        clone_url = self._clone_url_map.get(repo_name)
        if not clone_url:
            QMessageBox.warning(self, "Commit", "Repository URL not found. Load repos again.")
            return
        paths = [self.files_list.item(i).text() for i in range(self.files_list.count())]
        if not paths:
            QMessageBox.warning(self, "Commit", "Select at least one file.")
            return
        branch = self.branch_combo.currentData() or self.branch_combo.currentText() or None
        self.run_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setMaximum(len(paths))
        self.progress.setValue(0)
        self._worker = CommitWorker(acc, repo_name, branch, paths, clone_url, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_signal.connect(self._on_worker_finished)
        self._worker.start()

    def _on_progress(self, current: int, total: int, message: str):
        self.progress.setMaximum(total)
        self.progress.setValue(current)

    def _on_worker_finished(self):
        self.run_btn.setEnabled(True)
        self.progress.setVisible(False)
        QMessageBox.information(self, "Commit & Push", "Pipeline finished. Check Runs / Logs.")
