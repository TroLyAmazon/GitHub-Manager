namespace GitHubManager.Core.Domain;

public class Result
{
    public bool Success { get; set; }
    public string? ErrorMessage { get; set; }
}

public sealed class Result<T> : Result
{
    public T? Value { get; set; }

    public static Result<T> Ok(T value) => new() { Success = true, Value = value };
    public static Result<T> Fail(string message) => new() { Success = false, ErrorMessage = message };
}
