using System.Collections.Concurrent;
using System.Text;
using GitHubManager.Core.Domain;
using GitHubManager.Core.Interfaces;

namespace GitHubManager.Core.Services;

/// <summary>Orchestrates: for each file → copy to uploads, stage, commit, push. Stops on first failure.</summary>
public sealed class CommitPipeline
{
    private readonly ILocalStore _localStore;
    private readonly ISecretStore _secretStore;
    private readonly IGitService _gitService;
    private readonly IWorkspaceService _workspaceService;
    private readonly IGitHubApi _githubApi;

    public CommitPipeline(
        ILocalStore localStore,
        ISecretStore secretStore,
        IGitService gitService,
        IWorkspaceService workspaceService,
        IGitHubApi githubApi)
    {
        _localStore = localStore;
        _secretStore = secretStore;
        _gitService = gitService;
        _workspaceService = workspaceService;
        _githubApi = githubApi;
    }

    public async Task RunAsync(
        string accountId,
        string repoFullName,
        string cloneUrl,
        string branch,
        IReadOnlyList<string> sourceFilePaths,
        string commitMessagePrefix,
        string logFilePath,
        IProgress<PipelineProgress>? progress,
        CancellationToken ct)
    {
        var accounts = await _localStore.GetAccountsAsync(ct).ConfigureAwait(false);
        var account = accounts.FirstOrDefault(a => a.Id == accountId);
        if (account == null)
        {
            ReportFail(progress, 0, sourceFilePaths.Count, "Account not found.");
            return;
        }
        var token = _secretStore.Retrieve(account.SecretKey);
        if (string.IsNullOrEmpty(token))
        {
            ReportFail(progress, 0, sourceFilePaths.Count, "Token not found for account.");
            return;
        }

        var workspacePath = _workspaceService.GetWorkspacePath(accountId, repoFullName);
        await _gitService.EnsureCloneAsync(cloneUrl, workspacePath, token, ct).ConfigureAwait(false);

        var runs = new List<CommitRun>();
        var log = new StringBuilder();
        var runIdBase = DateTime.UtcNow.ToString("yyyyMMdd_HHmmss") + "_";

        for (var i = 0; i < sourceFilePaths.Count; i++)
        {
            if (ct.IsCancellationRequested)
                break;

            var sourcePath = sourceFilePaths[i];
            var fileName = Path.GetFileName(sourcePath);
            var targetFileName = PathPolicy.CleanFileName(fileName);
            _workspaceService.EnsureUploadsFolder(workspacePath);
            var uploadsDir = Path.Combine(workspacePath, PathPolicy.UploadsSegment);
            var uniqueFileName = PathPolicy.GetUniqueFileName(uploadsDir, targetFileName);
            var relInRepo = PathPolicy.UploadsSegment + "/" + uniqueFileName;

            progress?.Report(new PipelineProgress
            {
                FileIndex = i + 1,
                TotalFiles = sourceFilePaths.Count,
                CurrentFileName = fileName,
                Stage = "Preparing",
                Message = $"File {i + 1}/{sourceFilePaths.Count}: {fileName}"
            });

            if (_gitService.IsPathUnchanged(workspacePath, relInRepo))
            {
                log.AppendLine($"[{DateTime.Now:HH:mm:ss}] Skip (unchanged): {fileName}");
                runs.Add(new CommitRun
                {
                    Id = runIdBase + i,
                    AccountId = accountId,
                    RepoFullName = repoFullName,
                    Branch = branch,
                    FileName = fileName,
                    Status = "Skipped",
                    StartedAt = DateTime.UtcNow,
                    CompletedAt = DateTime.UtcNow
                });
                progress?.Report(new PipelineProgress
                {
                    FileIndex = i + 1,
                    TotalFiles = sourceFilePaths.Count,
                    CurrentFileName = fileName,
                    Stage = "Done",
                    Message = $"Skipped (unchanged): {fileName}"
                });
                continue;
            }

            try
            {
                relInRepo = _workspaceService.CopyToUploads(workspacePath, sourcePath, targetFileName);
            }
            catch (Exception ex)
            {
                log.AppendLine($"[{DateTime.Now:HH:mm:ss}] ERROR: {ex.Message}");
                var run = new CommitRun
                {
                    Id = runIdBase + i,
                    AccountId = accountId,
                    RepoFullName = repoFullName,
                    Branch = branch,
                    FileName = fileName,
                    Status = "Failed",
                    ErrorMessage = ex.Message,
                    StartedAt = DateTime.UtcNow,
                    CompletedAt = DateTime.UtcNow
                };
                runs.Add(run);
                await PersistRunsAndLogAsync(runs, log, logFilePath).ConfigureAwait(false);
                ReportFail(progress, i + 1, sourceFilePaths.Count, ex.Message);
                return;
            }

            var commitMessage = string.IsNullOrWhiteSpace(commitMessagePrefix)
                ? "Upload " + Path.GetFileName(relInRepo)
                : commitMessagePrefix.Trim() + " " + Path.GetFileName(relInRepo);

            progress?.Report(new PipelineProgress
            {
                FileIndex = i + 1,
                TotalFiles = sourceFilePaths.Count,
                CurrentFileName = fileName,
                Stage = "Packing",
                Message = $"Packing: {fileName}"
            });

            var runRecord = new CommitRun
            {
                Id = runIdBase + i,
                AccountId = accountId,
                RepoFullName = repoFullName,
                Branch = branch,
                FileName = fileName,
                Status = "Pending",
                StartedAt = DateTime.UtcNow,
                LogFilePath = logFilePath
            };
            runs.Add(runRecord);

            try
            {
                var prog = new Progress<PushProgressReport>(r =>
                {
                    progress?.Report(new PipelineProgress
                    {
                        FileIndex = i + 1,
                        TotalFiles = sourceFilePaths.Count,
                        CurrentFileName = fileName,
                        Stage = r.Stage,
                        BytesSent = r.BytesSent,
                        CurrentObjects = r.CurrentObjects,
                        TotalObjects = r.TotalObjects,
                        InstantSpeedBytesPerSec = r.InstantSpeedBytesPerSec,
                        AvgSpeedBytesPerSec = r.AvgSpeedBytesPerSec,
                        PeakSpeedBytesPerSec = r.PeakSpeedBytesPerSec,
                        Message = $"{r.Stage}: {fileName}"
                    });
                });

                var (sha, bytesSent, durationSec) = await _gitService.CommitAndPushAsync(
                    workspacePath,
                    branch,
                    relInRepo,
                    commitMessage,
                    token,
                    prog,
                    ct).ConfigureAwait(false);

                runRecord.Status = "Success";
                runRecord.Sha = sha;
                runRecord.CompletedAt = DateTime.UtcNow;
                runRecord.DurationSeconds = durationSec;
                runRecord.AvgSpeedMbps = durationSec > 0 ? (bytesSent / (1024.0 * 1024.0)) / durationSec : null;

                log.AppendLine($"[{DateTime.Now:HH:mm:ss}] OK: {fileName} -> {sha} ({durationSec:F1}s)");
            }
            catch (Exception ex)
            {
                runRecord.Status = "Failed";
                runRecord.ErrorMessage = ex.Message;
                runRecord.CompletedAt = DateTime.UtcNow;
                log.AppendLine($"[{DateTime.Now:HH:mm:ss}] FAIL: {fileName} - {ex.Message}");
                await PersistRunsAndLogAsync(runs, log, logFilePath).ConfigureAwait(false);
                ReportFail(progress, i + 1, sourceFilePaths.Count, ex.Message);
                return;
            }

            await PersistRunsAndLogAsync(runs, log, logFilePath).ConfigureAwait(false);
        }
    }

    private static void ReportFail(IProgress<PipelineProgress>? progress, int fileIndex, int total, string message)
    {
        progress?.Report(new PipelineProgress
        {
            FileIndex = fileIndex,
            TotalFiles = total,
            Stage = "Failed",
            Message = message,
            IsFailed = true
        });
    }

    private async Task PersistRunsAndLogAsync(List<CommitRun> runs, StringBuilder log, string logFilePath)
    {
        var existing = await _localStore.GetRunsAsync().ConfigureAwait(false);
        var sessionIds = runs.Select(r => r.Id).ToHashSet();
        var others = existing.Where(r => !sessionIds.Contains(r.Id)).ToList();
        var combined = runs.Concat(others).OrderByDescending(r => r.StartedAt).Take(500).ToList();
        await _localStore.SaveRunsAsync(combined).ConfigureAwait(false);

        Directory.CreateDirectory(Path.GetDirectoryName(logFilePath)!);
        await File.WriteAllTextAsync(logFilePath, log.ToString()).ConfigureAwait(false);
    }
}

public sealed class PipelineProgress
{
    public int FileIndex { get; set; }
    public int TotalFiles { get; set; }
    public string? CurrentFileName { get; set; }
    public string Stage { get; set; } = string.Empty;
    public string? Message { get; set; }
    public long BytesSent { get; set; }
    public long CurrentObjects { get; set; }
    public long TotalObjects { get; set; }
    public double InstantSpeedBytesPerSec { get; set; }
    public double AvgSpeedBytesPerSec { get; set; }
    public double PeakSpeedBytesPerSec { get; set; }
    public bool IsFailed { get; set; }
}
