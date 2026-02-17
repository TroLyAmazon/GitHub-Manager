using GitHubManager.Core.Domain;
using GitHubManager.Core.Interfaces;
using Octokit;

namespace GitHubManager.Core.Services;

public sealed class GitHubApiOctokit : IGitHubApi
{
    private static GitHubClient CreateClient(string token)
    {
        var client = new GitHubClient(new ProductHeaderValue("GitHubManager"));
        client.Credentials = new Credentials("x-access-token", token);
        return client;
    }

    public async Task<Result<(string Login, string? AvatarUrl)>> ValidateTokenAsync(string token, CancellationToken ct = default)
    {
        try
        {
            var client = CreateClient(token);
            var user = await client.User.Current().ConfigureAwait(false);
            return Result<(string, string?)>.Ok((user.Login, user.AvatarUrl));
        }
        catch (AuthorizationException ex)
        {
            return Result<(string, string?)>.Fail("Invalid token: " + ex.Message);
        }
        catch (Exception ex)
        {
            return Result<(string, string?)>.Fail("Validation failed: " + ex.Message);
        }
    }

    public async Task<Result<List<Repo>>> ListRepositoriesAsync(string token, CancellationToken ct = default)
    {
        try
        {
            var client = CreateClient(token);
            var repos = await client.Repository.GetAllForCurrent().ConfigureAwait(false);
            var list = repos.Select(r => new Repo
            {
                FullName = r.FullName,
                DefaultBranch = r.DefaultBranch ?? "main",
                IsPrivate = r.Private,
                CloneUrl = r.CloneUrl ?? ""
            }).ToList();
            return Result<List<Repo>>.Ok(list);
        }
        catch (AuthorizationException ex)
        {
            return Result<List<Repo>>.Fail("Access denied: " + ex.Message);
        }
        catch (Exception ex)
        {
            return Result<List<Repo>>.Fail("Failed to list repos: " + ex.Message);
        }
    }
}
