namespace GitHubManager.Core.Interfaces;

public interface IWorkspaceService
{
    /// <summary>Gets workspace path for account + repo: workspacesRoot/accountId/owner_repo</summary>
    string GetWorkspacePath(string accountId, string repoFullName);

    /// <summary>Ensures uploads/ folder exists in workspace. Returns full path to uploads dir.</summary>
    string EnsureUploadsFolder(string workspacePath);

    /// <summary>Copies source file to uploads folder with target filename (handles rename if exists: name (2).ext). Returns relative path "uploads/filename".</summary>
    string CopyToUploads(string workspacePath, string sourceFilePath, string targetFileName);
}
