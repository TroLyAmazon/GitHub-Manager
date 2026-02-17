namespace GitHubManager.Core.Utils;

public static class TimeUtil
{
    public static string FormatDuration(TimeSpan duration)
    {
        if (duration.TotalSeconds < 1)
            return $"{(int)(duration.TotalMilliseconds)} ms";
        if (duration.TotalSeconds < 60)
            return $"{duration.TotalSeconds:F1} s";
        return $"{(int)duration.TotalMinutes} m {duration.Seconds} s";
    }

    public static string FormatSpeedMbps(double bytesPerSec)
    {
        if (bytesPerSec <= 0) return "0 MB/s";
        return $"{bytesPerSec / (1024 * 1024):F2} MB/s";
    }
}
