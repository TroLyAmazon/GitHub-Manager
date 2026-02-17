namespace GitHubManager.Core.Interfaces;

public interface IGitService
{
    /// <summary>Ensures repo is cloned at workspacePath. Uses token for HTTPS auth (Username=x-access-token, Password=token).</summary>
    Task EnsureCloneAsync(string cloneUrl, string workspacePath, string token, CancellationToken ct = default);

    /// <summary>Stage single path (relative to repo root), commit with message, push. Returns (sha, bytesSent, durationSeconds) or throws.</summary>
    Task<(string Sha, long BytesSent, double DurationSeconds)> CommitAndPushAsync(
        string workspacePath,
        string branch,
        string relativePathInRepo,
        string commitMessage,
        string token,
        IProgress<PushProgressReport>? progress = null,
        CancellationToken ct = default);

    /// <summary>Returns true if working directory has no changes for the given path.</summary>
    bool IsPathUnchanged(string workspacePath, string relativePathInRepo);
}

public sealed class PushProgressReport
{
    public string Stage { get; set; } = string.Empty; // Packing, Uploading, Done
    public long CurrentObjects { get; set; }
    public long TotalObjects { get; set; }
    public long BytesSent { get; set; }
    public double InstantSpeedBytesPerSec { get; set; }
    public double AvgSpeedBytesPerSec { get; set; }
    public double PeakSpeedBytesPerSec { get; set; }
}
