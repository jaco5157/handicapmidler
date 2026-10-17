namespace InventoryService;

public record InventoryPaths(string InputDirectory, string OutputFile, string ExclusionFile)
{
    public static InventoryPaths Parse(string[] args)
    {
        const string usage = "Usage: --input-dir DIRECTORY --output-file FILE --exclude-file FILE";
        var options = new Dictionary<string, string>();
        var allowed = new[] { "--input-dir", "--output-file", "--exclude-file" };
        if (args.Length != 6)
            throw new ArgumentException(usage);

        for (var index = 0; index < args.Length; index += 2)
        {
            if (!allowed.Contains(args[index]) || string.IsNullOrWhiteSpace(args[index + 1]) ||
                args[index + 1].StartsWith("--") || !options.TryAdd(args[index], args[index + 1]))
                throw new ArgumentException(usage);
        }

        return new InventoryPaths(
            Path.GetFullPath(options["--input-dir"]),
            Path.GetFullPath(options["--output-file"]),
            Path.GetFullPath(options["--exclude-file"]));
    }
}