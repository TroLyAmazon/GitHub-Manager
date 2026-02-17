GitHubManager/
├─ GitHubManager.sln
├─ src/
│  ├─ GitHubManager.App/                     # WinUI 3 UI project
│  │  ├─ GitHubManager.App.csproj
│  │  ├─ App.xaml
│  │  ├─ App.xaml.cs
│  │  ├─ MainWindow.xaml
│  │  ├─ MainWindow.xaml.cs
│  │  ├─ Assets/
│  │  │  ├─ AppIcon.ico
│  │  │  └─ Images/
│  │  ├─ Styles/
│  │  │  ├─ Colors.xaml
│  │  │  └─ Typography.xaml
│  │  ├─ Controls/                           # Custom controls (Upload list item, log viewer...)
│  │  ├─ Views/                              # Pages (NavigationView destinations)
│  │  │  ├─ AccountsPage.xaml
│  │  │  ├─ AccountsPage.xaml.cs
│  │  │  ├─ ReposPage.xaml
│  │  │  ├─ ReposPage.xaml.cs
│  │  │  ├─ CommitPage.xaml
│  │  │  ├─ CommitPage.xaml.cs
│  │  │  ├─ RunsPage.xaml
│  │  │  └─ RunsPage.xaml.cs
│  │  ├─ ViewModels/                         # MVVM
│  │  │  ├─ MainViewModel.cs
│  │  │  ├─ AccountsViewModel.cs
│  │  │  ├─ ReposViewModel.cs
│  │  │  ├─ CommitViewModel.cs
│  │  │  └─ RunsViewModel.cs
│  │  ├─ Models/                             # UI-facing models (DTOs)
│  │  │  ├─ AccountItem.cs
│  │  │  ├─ RepoItem.cs
│  │  │  ├─ SelectedFileItem.cs
│  │  │  └─ RunItem.cs
│  │  ├─ Services/                           # UI services (navigation, dialogs, pickers)
│  │  │  ├─ NavigationService.cs
│  │  │  ├─ DialogService.cs
│  │  │  └─ FilePickerService.cs
│  │  └─ Helpers/
│  │     ├─ ObservableObject.cs
│  │     ├─ RelayCommand.cs
│  │     └─ UiThread.cs
│  │
│  ├─ GitHubManager.Core/                    # Business logic (no UI)
│  │  ├─ GitHubManager.Core.csproj
│  │  ├─ Domain/
│  │  │  ├─ Account.cs
│  │  │  ├─ Repo.cs
│  │  │  ├─ CommitRun.cs
│  │  │  └─ Result.cs
│  │  ├─ Interfaces/
│  │  │  ├─ ILocalStore.cs
│  │  │  ├─ ISecretStore.cs
│  │  │  ├─ IGitHubApi.cs
│  │  │  ├─ IGitService.cs
│  │  │  └─ IWorkspaceService.cs
│  │  ├─ Services/
│  │  │  ├─ LocalStoreJson.cs               # đọc/ghi JSON (atomic write)
│  │  │  ├─ SecretStoreWinCred.cs           # Credential Manager
│  │  │  ├─ GitHubApiOctokit.cs             # validate token, list repos
│  │  │  ├─ WorkspaceService.cs             # map repo -> local workspace path
│  │  │  ├─ GitServiceLibGit2Sharp.cs       # clone/commit/push + progress callbacks
│  │  │  ├─ CommitPipeline.cs               # loop từng file: stage->commit->push
│  │  │  └─ PathPolicy.cs                   # rule: luôn uploads/, rename trùng tên
│  │  └─ Utils/
│  │     ├─ JsonUtil.cs
│  │     ├─ HashUtil.cs
│  │     └─ TimeUtil.cs
│  │
│  └─ GitHubManager.Tests/                   # (optional) unit tests
│     ├─ GitHubManager.Tests.csproj
│     └─ ...
│
├─ build/
│  ├─ packaging/                             # MSIX packaging configs (optional)
│  └─ scripts/
│     └─ ...
└─ README.md