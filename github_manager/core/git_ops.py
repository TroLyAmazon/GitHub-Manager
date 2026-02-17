"""
Git operations via subprocess. HTTPS with PAT.
Clone, add, commit, push — one commit per file, push immediately.
"""
import os
import subprocess
import shutil

from . import store_json
from . import path_policy


def _run(
    cmd: list[str],
    cwd: str,
    env: dict | None = None,
    capture: bool = True,
) -> tuple[int, str, str]:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    try:
        r = subprocess.run(
            cmd,
            cwd=cwd,
            env=full_env,
            capture_output=capture,
            text=True,
            timeout=300,
        )
        return r.returncode, (r.stdout or ""), (r.stderr or "")
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -1, "", str(e)


def set_git_user(workspace_path: str, name: str, email: str) -> tuple[bool, str]:
    """
    Set git user.name and user.email for the repository.
    Returns (success, message).
    """
    code_name, out_name, err_name = _run(
        ["git", "config", "user.name", name],
        cwd=workspace_path,
    )
    if code_name != 0:
        return False, f"Failed to set user.name: {err_name}"
    
    code_email, out_email, err_email = _run(
        ["git", "config", "user.email", email],
        cwd=workspace_path,
    )
    if code_email != 0:
        return False, f"Failed to set user.email: {err_email}"
    
    return True, f"Git user configured: {name} <{email}>"


def clone_repo(clone_url: str, pat: str, workspace_path: str) -> tuple[bool, str]:
    """
    Clone via HTTPS with PAT in URL: https://<pat>@github.com/owner/repo.git
    Returns (success, message).
    """
    if workspace_path and os.path.exists(workspace_path) and os.listdir(workspace_path):
        return True, "Already cloned"
    # Ensure parent exists and path is empty for clone
    parent = os.path.dirname(workspace_path)
    os.makedirs(parent, exist_ok=True)
    if os.path.exists(workspace_path):
        shutil.rmtree(workspace_path)
    # https://github.com/owner/repo -> https://TOKEN@github.com/owner/repo
    if "https://" in clone_url and "@" not in clone_url:
        auth_url = clone_url.replace("https://", f"https://{pat}@", 1)
    else:
        auth_url = clone_url
    code, out, err = _run(
        ["git", "clone", auth_url, workspace_path],
        cwd=parent,
    )
    msg = (out + "\n" + err).strip() or f"Exit code {code}"
    return code == 0, msg


def add_commit_push(
    workspace_path: str,
    rel_path: str,
    commit_message: str,
    pat: str,
    user_name: str = "",
    user_email: str = "",
    remote_name: str = "origin",
    branch: str | None = None,
) -> tuple[bool, str, str]:
    """
    git add <rel_path>, git commit -m "...", git push.
    If user_name and user_email are provided, set repo git config and pass
    GIT_AUTHOR_* / GIT_COMMITTER_* env for the commit so the commit author
    is always the account (not global git config).
    Returns (success, commit_sha, stderr_or_message).
    commit_sha is empty if failed.
    """
    # Set git user in repo if provided (for consistency)
    if user_name and user_email:
        ok, msg = set_git_user(workspace_path, user_name, user_email)
        if not ok:
            return False, "", msg

    # Env for git commit: override any global/local config so contributions
    # go to the account, not the machine's default user (e.g. adcampusidentity).
    commit_env = None
    if user_name and user_email:
        commit_env = {
            "GIT_AUTHOR_NAME": user_name,
            "GIT_AUTHOR_EMAIL": user_email,
            "GIT_COMMITTER_NAME": user_name,
            "GIT_COMMITTER_EMAIL": user_email,
        }

    code, out, err = _run(["git", "add", rel_path], cwd=workspace_path)
    if code != 0:
        return False, "", (out + "\n" + err).strip()

    code, out, err = _run(
        ["git", "commit", "-m", commit_message],
        cwd=workspace_path,
        env=commit_env,
    )
    if code != 0:
        return False, "", (out + "\n" + err).strip()

    # Get commit SHA
    code_sha, out_sha, _ = _run(
        ["git", "rev-parse", "HEAD"],
        cwd=workspace_path,
    )
    commit_sha = out_sha.strip() if code_sha == 0 else ""

    # Push with PAT in URL (strip any existing credentials)
    remote_url = _get_remote_url(workspace_path, remote_name)
    if not remote_url:
        return False, commit_sha, "Could not get remote URL"
    if "@" in remote_url:
        push_url = "https://" + pat + "@" + remote_url.split("@", 1)[1]
    elif remote_url.startswith("https://"):
        push_url = remote_url.replace("https://", f"https://{pat}@", 1)
    else:
        push_url = remote_url
    push_branch = branch or _get_default_branch(workspace_path)
    code, out, err = _run(
        ["git", "push", push_url, push_branch],
        cwd=workspace_path,
    )
    if code != 0:
        return False, commit_sha, (out + "\n" + err).strip()
    return True, commit_sha, ""


def _get_remote_url(workspace_path: str, remote: str) -> str | None:
    code, out, _ = _run(
        ["git", "config", "--get", f"remote.{remote}.url"],
        cwd=workspace_path,
    )
    return out.strip() if code == 0 else None


def _get_default_branch(workspace_path: str) -> str:
    code, out, _ = _run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=workspace_path,
    )
    return out.strip() if code == 0 else "main"


def checkout_branch(workspace_path: str, branch: str) -> tuple[bool, str]:
    """Checkout branch. Returns (success, message)."""
    code, out, err = _run(
        ["git", "checkout", branch],
        cwd=workspace_path,
    )
    msg = (out + "\n" + err).strip() or f"Exit code {code}"
    return code == 0, msg


def get_branches(workspace_path: str) -> list[str]:
    """List local branch names."""
    code, out, _ = _run(
        ["git", "branch", "--format=%(refname:short)"],
        cwd=workspace_path,
    )
    if code != 0:
        return []
    return [s.strip() for s in out.strip().splitlines() if s.strip()]
