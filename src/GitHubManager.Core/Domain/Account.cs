namespace GitHubManager.Core.Domain;

public sealed class Account
{
    public string Id { get; set; } = string.Empty;
    public string Label { get; set; } = string.Empty;
    /// <summary>Secret key used to retrieve token from Credential Manager. Token is NOT stored in JSON.</summary>
    public string SecretKey { get; set; } = string.Empty;
    public string? Login { get; set; }
    public string? AvatarUrl { get; set; }
}
