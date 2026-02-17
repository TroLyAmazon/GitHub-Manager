github_manager/
├─ app.py                      # entry
├─ ui/                         # Qt UI
│  ├─ main_window.py
│  ├─ accounts_page.py
│  ├─ repos_page.py
│  ├─ commit_page.py
│  └─ runs_page.py
├─ core/
│  ├─ store_json.py            # accounts.json, runs.json
│  ├─ secrets.py               # keyring save/load token
│  ├─ github_api.py            # list repos (REST)
│  ├─ git_ops.py               # clone/commit/push (git CLI)
│  └─ path_policy.py           # uploads/<filename>, rename trùng
├─ assets/
├─ requirements.txt
└─ build.spec                  # PyInstaller spec (optional)