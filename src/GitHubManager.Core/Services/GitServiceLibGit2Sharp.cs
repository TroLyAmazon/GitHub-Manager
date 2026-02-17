using System.Diagnostics;
using LibGit2Sharp;
using LibGit2Sharp.Handlers;
using GitHubManager.Core.Interfaces;

namespace GitHubManager.Core.Services;

public sealed class GitServiceLibGit2Sharp : IGitService
{
    public async Task EnsureCloneAsync(string cloneUrl, string workspacePath, string token, CancellationToken ct = default)
    {
        if (Directory.Exists(Path.Combine(workspacePath, ".git")))
            return;

        await Task.Run(() =>
        {
            var co = new CloneOptions();
            co.FetchOptions.CredentialsProvider = (_, _, _) => new UsernamePasswordCredentials
            {
                Username = "x-access-token",
                Password = token
            };
            Repository.Clone(cloneUrl, workspacePath, co);
        }, ct).ConfigureAwait(false);
    }

    public bool IsPathUnchanged(string workspacePath, string relativePathInRepo)
    {
        var fullPath = Path.Combine(workspacePath, relativePathInRepo.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(fullPath))
            return true;

        using var repo = new Repository(workspacePath);
        var status = repo.RetrieveStatus(new StatusOptions { IncludeUntracked = true });
        var entry = status[relativePathInRepo.Replace('\\', '/')];
        if (entry == null)
            return true;
        return (entry?.State ?? (FileStatus)0) == 0;
    }

    public async Task<(string Sha, long BytesSent, double DurationSeconds)> CommitAndPushAsync(
        string workspacePath,
        string branch,
        string relativePathInRepo,
        string commitMessage,
        string token,
        IProgress<PushProgressReport>? progress = null,
        CancellationToken ct = default)
    {
        return await Task.Run(() =>
        {
            using var repo = new Repository(workspacePath);
            var sw = Stopwatch.StartNew();
            long bytesSent = 0;
            long lastBytes = 0;
            var lastTime = sw.Elapsed;
            double instantSpeed = 0, avgSpeed = 0, peakSpeed = 0;
            var lockObj = new object();

            EnsureBranchCheckedOut(repo, branch);

            var sig = new Signature("GitHub Manager", "noreply@localhost", DateTimeOffset.UtcNow);

            repo.Index.Add(relativePathInRepo.Replace('\\', '/'));
            repo.Index.Write();

            var commit = repo.Commit(commitMessage, sig, sig);
            var sha = commit.Sha;

            var pushOptions = new PushOptions
            {
                CredentialsProvider = (_, _, _) => new UsernamePasswordCredentials
                {
                    Username = "x-access-token",
                    Password = token
                },
                OnPackBuilderProgress = (stage, current, total) =>
                {
                    progress?.Report(new PushProgressReport
                    {
                        Stage = stage.ToString(),
                        CurrentObjects = current,
                        TotalObjects = total,
                        BytesSent = bytesSent,
                        InstantSpeedBytesPerSec = instantSpeed,
                        AvgSpeedBytesPerSec = avgSpeed,
                        PeakSpeedBytesPerSec = peakSpeed
                    });
                    return !ct.IsCancellationRequested;
                },
                OnPushTransferProgress = (current, total, bytes) =>
                {
                    lock (lockObj)
                    {
                        bytesSent = bytes;
                        var now = sw.Elapsed;
                        var deltaBytes = bytes - lastBytes;
                        var deltaSec = (now - lastTime).TotalSeconds;
                        if (deltaSec > 0.01)
                        {
                            instantSpeed = deltaBytes / deltaSec;
                            lastBytes = bytes;
                            lastTime = now;
                        }
                        if (now.TotalSeconds > 0)
                            avgSpeed = bytes / now.TotalSeconds;
                        if (instantSpeed > peakSpeed)
                            peakSpeed = instantSpeed;
                    }
                    progress?.Report(new PushProgressReport
                    {
                        Stage = "Uploading",
                        CurrentObjects = current,
                        TotalObjects = total,
                        BytesSent = bytesSent,
                        InstantSpeedBytesPerSec = instantSpeed,
                        AvgSpeedBytesPerSec = avgSpeed,
                        PeakSpeedBytesPerSec = peakSpeed
                    });
                    return !ct.IsCancellationRequested;
                }
            };

            var remote = repo.Network.Remotes["origin"];
            if (remote == null)
                throw new InvalidOperationException("Remote 'origin' not found.");
            var refSpec = "refs/heads/" + branch;
            repo.Network.Push(remote, refSpec, pushOptions);

            progress?.Report(new PushProgressReport
            {
                Stage = "Done",
                BytesSent = bytesSent,
                AvgSpeedBytesPerSec = avgSpeed,
                PeakSpeedBytesPerSec = peakSpeed
            });

            sw.Stop();
            return (sha, bytesSent, sw.Elapsed.TotalSeconds);
        }, ct).ConfigureAwait(false);
    }

    private static void EnsureBranchCheckedOut(Repository repo, string branch)
    {
        if (repo.Head.FriendlyName == branch)
            return;
        var b = repo.Branches[branch];
        if (b != null)
        {
            Commands.Checkout(repo, b);
            return;
        }
        var remoteBranch = repo.Branches["origin/" + branch];
        if (remoteBranch != null)
        {
            var local = repo.CreateBranch(branch, remoteBranch.Tip);
            repo.Branches.Update(local, b => b.TrackedBranch = remoteBranch.CanonicalName);
            Commands.Checkout(repo, local);
            return;
        }
        var head = repo.Head;
        var newBranch = repo.CreateBranch(branch, head.Tip);
        Commands.Checkout(repo, newBranch);
    }
}
