using GitHubManager.Core.Domain;

namespace GitHubManager.Core.Interfaces;

public interface ILocalStore
{
    string DataDirectory { get; }
    string LogsDirectory { get; }
    string WorkspacesRoot { get; }

    Task<List<Account>> GetAccountsAsync(CancellationToken ct = default);
    Task SaveAccountsAsync(IReadOnlyList<Account> accounts, CancellationToken ct = default);

    Task<List<CommitRun>> GetRunsAsync(CancellationToken ct = default);
    Task SaveRunsAsync(IReadOnlyList<CommitRun> runs, CancellationToken ct = default);

    Task<Dictionary<string, string>> GetSettingsAsync(CancellationToken ct = default);
    Task SaveSettingsAsync(Dictionary<string, string> settings, CancellationToken ct = default);
}
