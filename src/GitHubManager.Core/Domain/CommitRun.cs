namespace GitHubManager.Core.Domain;

public sealed class CommitRun
{
    public string Id { get; set; } = string.Empty;
    public string AccountId { get; set; } = string.Empty;
    public string RepoFullName { get; set; } = string.Empty;
    public string Branch { get; set; } = string.Empty;
    public string FileName { get; set; } = string.Empty;
    public string Status { get; set; } = "Pending"; // Pending, Success, Failed, Skipped
    public string? Sha { get; set; }
    public string? ErrorMessage { get; set; }
    public DateTime StartedAt { get; set; }
    public DateTime? CompletedAt { get; set; }
    public double? DurationSeconds { get; set; }
    public double? AvgSpeedMbps { get; set; }
    public string? LogFilePath { get; set; }
}
