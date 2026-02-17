namespace GitHubManager.Core.Domain;

public sealed class Repo
{
    public string FullName { get; set; } = string.Empty;
    public string DefaultBranch { get; set; } = string.Empty;
    public bool IsPrivate { get; set; }
    public string CloneUrl { get; set; } = string.Empty;
}
