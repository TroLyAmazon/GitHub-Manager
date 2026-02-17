# GitHub Manager

WinUI 3 (.NET 8) desktop app to manage multiple GitHub accounts (Fine-grained PAT), list repositories, and commit/push multiple files—each as a separate commit under `uploads/`—with real-time push progress and upload speed.

## Requirements

- Windows 10 1809+ / Windows 11
- .NET 8 SDK
- No need for Git.exe; uses LibGit2Sharp and Octokit

## Build

**Recommended:** Open `GitHubManager.sln` in **Visual Studio 2022** (with "Desktop development with C++" or Windows SDK workload) and build from there (F6). This avoids known XAML compiler issues when using `dotnet build` from CLI.

From command line:

```bash
cd d:\Desktop\GitHub-Manager
dotnet restore
dotnet build -c Release -p:Platform=x64
```

If XamlCompiler fails with exit code 1 (no diagnostic output), build from Visual Studio or ensure Windows SDK 10.0.22621+ is installed.

## Run

```bash
dotnet run --project src\GitHubManager.App\GitHubManager.App.csproj -c Release
```

Or from Visual Studio: set **GitHubManager.App** as startup project and run (F5).

## Publish (single-file executable)

```bash
dotnet publish src\GitHubManager.App\GitHubManager.App.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -o build\publish
```

Output: `build\publish\GitHubManager.exe`

For ARM64:

```bash
dotnet publish src\GitHubManager.App\GitHubManager.App.csproj -c Release -r win-arm64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -o build\publish-arm64
```

## Features

- **Accounts**: Add account by label + Fine-grained PAT. Token is validated (GET /user) and stored in **Windows Credential Manager**; only a secret key is stored in JSON.
- **Repositories**: Select account → load repo list (full name, default branch, private/public).
- **Commit & Push**: Select account, repo, branch; pick multiple files; each file is copied to `uploads/` (renamed if duplicate: `name (2).ext`), committed alone, then pushed. Unchanged files are skipped. Progress shows file index, stage (Packing/Uploading/Done), bytes sent, and upload speed (MB/s).
- **Runs/Logs**: List recent runs (file, repo, status, sha, duration, avg speed). Open log file on demand.

## Data locations

- **Data**: `%LOCALAPPDATA%\GitHubManager\data\` (accounts.json, runs.json, settings.json)
- **Logs**: `%LOCALAPPDATA%\GitHubManager\logs\`
- **Workspaces**: `%LOCALAPPDATA%\GitHubManager\workspaces\<accountId>\<owner_repo>\`

## Solution structure

```
GitHubManager/
├── GitHubManager.sln
├── src/
│   ├── GitHubManager.App/     # WinUI 3 app
│   └── GitHubManager.Core/    # Domain, services (Octokit, LibGit2Sharp, Credential Manager)
├── build/
└── README.md
```

## License

MIT.
