using System.Collections.Concurrent;
using GitHubManager.Core.Domain;
using GitHubManager.Core.Interfaces;
using GitHubManager.Core.Utils;

namespace GitHubManager.Core.Services;

public sealed class LocalStoreJson : ILocalStore
{
    private readonly string _baseDir;
    private readonly ConcurrentDictionary<string, byte> _locks = new();

    public LocalStoreJson()
    {
        _baseDir = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "GitHubManager");
    }

    public string DataDirectory => Path.Combine(_baseDir, "data");
    public string LogsDirectory => Path.Combine(_baseDir, "logs");
    public string WorkspacesRoot => Path.Combine(_baseDir, "workspaces");

    private string AccountsPath => Path.Combine(DataDirectory, "accounts.json");
    private string RunsPath => Path.Combine(DataDirectory, "runs.json");
    private string SettingsPath => Path.Combine(DataDirectory, "settings.json");

    private async Task<T> ReadJsonAsync<T>(string path, T defaultValue, CancellationToken ct) where T : class
    {
        if (!File.Exists(path))
            return defaultValue;
        try
        {
            var json = await File.ReadAllTextAsync(path, ct).ConfigureAwait(false);
            var result = JsonUtil.Deserialize<T>(json);
            return result ?? defaultValue;
        }
        catch
        {
            return defaultValue;
        }
    }

    public async Task<List<Account>> GetAccountsAsync(CancellationToken ct = default)
    {
        var list = await ReadJsonAsync<List<Account>>(AccountsPath, new List<Account>(), ct).ConfigureAwait(false);
        return list ?? new List<Account>();
    }

    public async Task SaveAccountsAsync(IReadOnlyList<Account> accounts, CancellationToken ct = default)
    {
        Directory.CreateDirectory(DataDirectory);
        var json = JsonUtil.Serialize(accounts.ToList());
        await JsonUtil.WriteAllTextAtomicAsync(AccountsPath, json, ct).ConfigureAwait(false);
    }

    public async Task<List<CommitRun>> GetRunsAsync(CancellationToken ct = default)
    {
        var list = await ReadJsonAsync<List<CommitRun>>(RunsPath, new List<CommitRun>(), ct).ConfigureAwait(false);
        return list ?? new List<CommitRun>();
    }

    public async Task SaveRunsAsync(IReadOnlyList<CommitRun> runs, CancellationToken ct = default)
    {
        Directory.CreateDirectory(DataDirectory);
        var json = JsonUtil.Serialize(runs.ToList());
        await JsonUtil.WriteAllTextAtomicAsync(RunsPath, json, ct).ConfigureAwait(false);
    }

    public async Task<Dictionary<string, string>> GetSettingsAsync(CancellationToken ct = default)
    {
        var dict = await ReadJsonAsync<Dictionary<string, string>>(SettingsPath, new Dictionary<string, string>(), ct).ConfigureAwait(false);
        return dict ?? new Dictionary<string, string>();
    }

    public async Task SaveSettingsAsync(Dictionary<string, string> settings, CancellationToken ct = default)
    {
        Directory.CreateDirectory(DataDirectory);
        var json = JsonUtil.Serialize(settings);
        await JsonUtil.WriteAllTextAtomicAsync(SettingsPath, json, ct).ConfigureAwait(false);
    }
}
