using GitHubManager.Core.Domain;

namespace GitHubManager.Core.Interfaces;

public interface IGitHubApi
{
    /// <summary>Validates token and returns user login + avatar URL.</summary>
    Task<Result<(string Login, string? AvatarUrl)>> ValidateTokenAsync(string token, CancellationToken ct = default);

    /// <summary>Lists repositories for the authenticated user.</summary>
    Task<Result<List<Repo>>> ListRepositoriesAsync(string token, CancellationToken ct = default);
}
