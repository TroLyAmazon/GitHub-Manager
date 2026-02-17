using System.Text.Json;

namespace GitHubManager.Core.Utils;

public static class JsonUtil
{
    private static readonly JsonSerializerOptions Options = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = true
    };

    public static string Serialize<T>(T value) => JsonSerializer.Serialize(value, Options);

    public static T? Deserialize<T>(string json) => JsonSerializer.Deserialize<T>(json, Options);

    /// <summary>Atomic write: write to temp file then replace target.</summary>
    public static async Task WriteAllTextAtomicAsync(string filePath, string contents, CancellationToken ct = default)
    {
        var dir = Path.GetDirectoryName(filePath);
        if (!string.IsNullOrEmpty(dir))
            Directory.CreateDirectory(dir);
        var tempPath = filePath + ".tmp." + Guid.NewGuid().ToString("N")[..8];
        await File.WriteAllTextAsync(tempPath, contents, ct).ConfigureAwait(false);
        try
        {
            File.Move(tempPath, filePath, overwrite: true);
        }
        catch
        {
            if (File.Exists(tempPath))
                File.Delete(tempPath);
            throw;
        }
    }
}
