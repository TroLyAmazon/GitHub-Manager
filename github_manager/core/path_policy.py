"""
Path rules for commit uploads: fixed base uploads/, clean filenames, dedupe.
"""
import os
import re

UPLOADS_BASE = "uploads"


def clean_filename(name: str) -> str:
    """Remove invalid filename chars for Windows/Git."""
    # Keep alphanumeric, dot, hyphen, underscore, space
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name)
    return name.strip() or "file"


def resolve_upload_path(uploads_dir: str, desired_name: str, existing_names: set[str]) -> tuple[str, str]:
    """
    Given uploads_dir (absolute path to repo's uploads/), desired filename,
    and set of already-used names in that folder, return:
    (absolute_path, relative_path_for_commit e.g. uploads/filename.ext)

    Dedupe: file.ext -> file (2).ext -> file (3).ext ...
    """
    base = desired_name
    stem, ext = os.path.splitext(base)
    if not stem:
        stem, ext = "file", ext or ""
    candidate = base
    n = 2
    while candidate in existing_names:
        candidate = f"{stem} ({n}){ext}"
        n += 1
    existing_names.add(candidate)
    abs_path = os.path.join(uploads_dir, candidate)
    rel_path = f"{UPLOADS_BASE}/{candidate}"
    return abs_path, rel_path


def ensure_upload_dir(workspace_path: str) -> str:
    """Ensure uploads/ exists in workspace; return its absolute path."""
    uploads = os.path.join(workspace_path, UPLOADS_BASE)
    os.makedirs(uploads, exist_ok=True)
    return uploads
