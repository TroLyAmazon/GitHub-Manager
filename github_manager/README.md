# GitHub Manager

A local-only Windows desktop application to manage GitHub accounts via Fine-grained Personal Access Tokens (PAT), list repositories, and commit selected files to `uploads/<filename>` with one commit and one push per file.

## Requirements

- Python 3.11+
- Windows (uses %LOCALAPPDATA% and Windows Credential Manager via keyring)

## Setup

1. Create a virtual environment (recommended):

   ```bash
   cd github_manager
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Run

From the `github_manager` directory:

```bash
python app.py
```

## Build executable

Single-file executable, no console window:

```bash
cd github_manager
pyinstaller --noconsole --onefile --name GitHubManager app.py
```

Output: `dist/GitHubManager.exe`

Optional: use the provided spec file for more control:

```bash
pyinstaller GitHubManager.spec
```

## Features

- **Accounts**: Add GitHub accounts with a PAT (stored in Windows Credential Manager). No username/password.
- **Repositories**: Select an account and load repositories (full name, visibility, default branch).
- **Commit & Push**: Select account, repository, branch, and multiple files. Each file is committed under `uploads/<filename>` (with safe names and deduplication) and pushed immediately (one commit per file).
- **Runs / Logs**: View run history and log paths.

## Data location

- `%LOCALAPPDATA%\GitHubManager\`
  - `data/accounts.json` – account metadata (no tokens)
  - `data/runs.json` – run history
  - `logs/` – per-run log files
  - `workspaces/<accountId>/<owner_repo>/` – cloned repos and uploads
