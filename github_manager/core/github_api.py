"""
GitHub REST API client using PAT. No username/password.
"""
import requests

API_BASE = "https://api.github.com"


def get_user(token: str) -> dict | None:
    """
    GET /user. Returns user dict or None on failure.
    """
    resp = requests.get(
        f"{API_BASE}/user",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        },
        timeout=15,
    )
    if resp.status_code != 200:
        return None
    return resp.json()


def get_user_emails(token: str) -> list[dict] | None:
    """
    GET /user/emails. Cần PAT có scope user:email (classic) hoặc Email: Read (fine-grained).
    Returns list of {"email", "primary", "verified", ...} or None.
    """
    resp = requests.get(
        f"{API_BASE}/user/emails",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        },
        timeout=15,
    )
    if resp.status_code != 200:
        return None
    return resp.json()


def get_latest_release(owner: str, repo: str) -> dict | None:
    """
    Lấy bản phát hành mới nhất. Public API, không cần token.
    Thử /releases/latest trước; nếu 404 (vd. chỉ có pre-release) thì dùng /releases (bản đầu tiên = mới nhất, kể cả pre-release).
    Returns release dict (tag_name, html_url, body, ...) or None.
    """
    headers = {"Accept": "application/vnd.github.v3+json"}
    resp = requests.get(
        f"{API_BASE}/repos/{owner}/{repo}/releases/latest",
        headers=headers,
        timeout=15,
    )
    if resp.status_code == 200:
        return resp.json()
    # 404 khi chưa có release hoặc chỉ có pre-release → lấy danh sách releases, bản đầu = mới nhất
    if resp.status_code == 404:
        resp_list = requests.get(
            f"{API_BASE}/repos/{owner}/{repo}/releases",
            params={"per_page": 1},
            headers=headers,
            timeout=15,
        )
        if resp_list.status_code == 200:
            data = resp_list.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0]
    return None


def get_repos(token: str, per_page: int = 100) -> list[dict] | None:
    """
    GET /user/repos. Returns list of repo dicts or None on failure.
    """
    resp = requests.get(
        f"{API_BASE}/user/repos",
        params={"per_page": per_page},
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        },
        timeout=15,
    )
    if resp.status_code != 200:
        return None
    return resp.json()
