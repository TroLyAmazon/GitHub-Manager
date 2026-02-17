using CredentialManagement;
using GitHubManager.Core.Interfaces;

namespace GitHubManager.Core.Services;

public sealed class SecretStoreWinCred : ISecretStore
{
    private const string TargetPrefix = "GitHubManager_";

    private static string TargetName(string key) => TargetPrefix + key;

    public void Store(string key, string secret)
    {
        using var cred = new Credential
        {
            Target = TargetName(key),
            Type = CredentialType.Generic,
            Username = key,
            Password = secret,
            PersistanceType = PersistanceType.LocalComputer
        };
        cred.Save();
    }

    public string? Retrieve(string key)
    {
        using var cred = new Credential { Target = TargetName(key) };
        return cred.Load() ? cred.Password : null;
    }

    public void Delete(string key)
    {
        using var cred = new Credential { Target = TargetName(key) };
        cred.Delete();
    }

    public bool Exists(string key)
    {
        using var cred = new Credential { Target = TargetName(key) };
        return cred.Exists();
    }
}
