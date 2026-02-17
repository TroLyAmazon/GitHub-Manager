namespace GitHubManager.Core.Interfaces;

public interface ISecretStore
{
    void Store(string key, string secret);
    string? Retrieve(string key);
    void Delete(string key);
    bool Exists(string key);
}
