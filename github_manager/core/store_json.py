"""
Atomic JSON read/write for GitHubManager local storage.
Storage root: %LOCALAPPDATA%\\GitHubManager\\
"""
import json
import os
import tempfile


def get_app_data_root() -> str:
    """Return %LOCALAPPDATA%\\GitHubManager\\"""
    root = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    path = os.path.join(root, "GitHubManager")
    os.makedirs(path, exist_ok=True)
    return path


def get_data_dir() -> str:
    """Return .../GitHubManager/data/"""
    path = os.path.join(get_app_data_root(), "data")
    os.makedirs(path, exist_ok=True)
    return path


def get_logs_dir() -> str:
    """Return .../GitHubManager/logs/"""
    path = os.path.join(get_app_data_root(), "logs")
    os.makedirs(path, exist_ok=True)
    return path


def get_workspaces_dir() -> str:
    """Return .../GitHubManager/workspaces/"""
    path = os.path.join(get_app_data_root(), "workspaces")
    os.makedirs(path, exist_ok=True)
    return path


def get_workspace_path(account_id: str, owner_repo: str) -> str:
    """Return .../workspaces/<accountId>/<owner_repo>/"""
    base = get_workspaces_dir()
    path = os.path.join(base, account_id, owner_repo.replace("/", "_"))
    os.makedirs(path, exist_ok=True)
    return path


def _path_under_data(filename: str) -> str:
    return os.path.join(get_data_dir(), filename)


def read_json(filename: str) -> dict | list:
    """Read JSON from data/<filename>. Returns {} or [] if missing."""
    path = _path_under_data(filename)
    if not os.path.isfile(path):
        return {} if not filename.endswith("runs.json") else []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {} if not filename.endswith("runs.json") else []


def write_json(filename: str, data: dict | list) -> None:
    """Atomic write JSON to data/<filename>."""
    path = _path_under_data(filename)
    dirpath = os.path.dirname(path)
    os.makedirs(dirpath, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dirpath, prefix=".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
