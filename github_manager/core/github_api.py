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
