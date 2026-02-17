using GitHubManager.Core.Interfaces;

namespace GitHubManager.Core.Services;

public sealed class WorkspaceService : IWorkspaceService
{
    private readonly ILocalStore _store;

    public WorkspaceService(ILocalStore store)
    {
        _store = store;
    }

    public string GetWorkspacePath(string accountId, string repoFullName)
    {
        var safe = repoFullName.Replace("/", "_");
        return Path.Combine(_store.WorkspacesRoot, accountId, safe);
    }

    public string EnsureUploadsFolder(string workspacePath)
    {
        var uploads = Path.Combine(workspacePath, PathPolicy.UploadsSegment);
        Directory.CreateDirectory(uploads);
        return uploads;
    }

    public string CopyToUploads(string workspacePath, string sourceFilePath, string targetFileName)
    {
        var uploads = EnsureUploadsFolder(workspacePath);
        var uniqueName = PathPolicy.GetUniqueFileName(uploads, targetFileName);
        var destPath = Path.Combine(uploads, uniqueName);
        File.Copy(sourceFilePath, destPath, overwrite: true);
        return PathPolicy.UploadsSegment + "/" + uniqueName;
    }
}
