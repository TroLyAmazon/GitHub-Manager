namespace GitHubManager.Core;

/// <summary>Fixed repo path: uploads/&lt;filename&gt;. Handles safe filenames and duplicate naming.</summary>
public static class PathPolicy
{
    public const string UploadsSegment = "uploads";
    public static string UploadsPrefix => UploadsSegment + "/";

    private static readonly char[] InvalidChars = Path.GetInvalidFileNameChars()
        .Concat(new[] { ':', '*', '?', '"', '<', '>', '|', '\\' }).Distinct().ToArray();

    /// <summary>Cleans filename: remove invalid chars, forbid directory traversal.</summary>
    public static string CleanFileName(string fileName)
    {
        if (string.IsNullOrWhiteSpace(fileName))
            return "file";
        var name = Path.GetFileName(fileName);
        foreach (var c in InvalidChars)
            name = name.Replace(c, '_');
        if (string.IsNullOrWhiteSpace(name))
            return "file";
        return name;
    }

    /// <summary>Repo path for a file: always use "/" separators.</summary>
    public static string ToRepoPath(string fileName) => UploadsSegment + "/" + CleanFileName(fileName);

    /// <summary>Generates unique name if file exists: "name (2).ext", "name (3).ext", etc.</summary>
    public static string GetUniqueFileName(string directory, string desiredFileName)
    {
        var clean = CleanFileName(desiredFileName);
        var path = Path.Combine(directory, clean);
        if (!File.Exists(path))
            return clean;
        var stem = Path.GetFileNameWithoutExtension(clean);
        var ext = Path.GetExtension(clean);
        for (var i = 2; i < 10000; i++)
        {
            var candidate = stem + " (" + i + ")" + ext;
            var candidatePath = Path.Combine(directory, candidate);
            if (!File.Exists(candidatePath))
                return candidate;
        }
        return stem + "_" + Guid.NewGuid().ToString("N")[..8] + ext;
    }
}
