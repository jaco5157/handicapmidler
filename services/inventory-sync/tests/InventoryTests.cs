using System.Xml.Linq;
using InventoryService.DataProviders;
using InventoryService.Models;
using Xunit;

namespace InventoryService.Tests;

public class InventoryTests : IDisposable
{
    private readonly string directory = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());

    public InventoryTests() => Directory.CreateDirectory(directory);

    [Fact]
    public void PathsResolveExplicitArguments()
    {
        var paths = InventoryPaths.Parse(new[]
        {
            "--input-dir", "input", "--exclude-file", "exclude.txt", "--output-file", "output/document.xml"
        });
        Assert.Equal(Path.GetFullPath("input"), paths.InputDirectory);
        Assert.Equal(Path.GetFullPath("exclude.txt"), paths.ExclusionFile);
        Assert.Equal(Path.GetFullPath("output/document.xml"), paths.OutputFile);
    }

    [Theory]
    [InlineData()]
    [InlineData("--input-dir", "input")]
    [InlineData("--input-dir", "input", "--input-dir", "other", "--output-file", "file")]
    [InlineData("--unknown", "input", "--exclude-file", "exclude", "--output-file", "file")]
    public void MissingOrInvalidPathsFail(params string[] args) =>
        Assert.Throws<ArgumentException>(() => InventoryPaths.Parse(args));

    [Fact]
    public void ExplicitPathsPreserveBaselineXmlAndExclusions()
    {
        var input = Path.Combine(directory, "supplier");
        Directory.CreateDirectory(input);
        File.WriteAllText(Path.Combine(input, "varer.LST"), "1;BASELINE-001\n2;BASELINE-002\n3;3020S8\n");
        File.WriteAllText(Path.Combine(input, "lagerbehold.LST"), "1;7\n2;0\n3;99\n");
        File.WriteAllText(Path.Combine(input, "lagerbevaeg.LST"), "2;;15-10-26;5\n");
        var exclusions = Path.Combine(directory, "exclude.txt");
        File.WriteAllText(exclusions, "3020S8\n");
        var output = Path.Combine(directory, "upload", "document.xml");

        var items = new CSVDataProvider(input).GetInventoryItems();
        new XMLDataProvider(output, exclusions).GenerateInventoryFile(items);

        var expected = XElement.Parse("""
            <PRODUCT_EXPORT type="PRODUCTS"><ELEMENTS>
              <PRODUCT><GENERAL><PROD_NUM>BASELINE-001</PROD_NUM><LANGUAGE_ID>26</LANGUAGE_ID></GENERAL>
                <STOCK><STOCK_COUNT>7</STOCK_COUNT><PROD_DELIVERY_NOT_IN_STOCK>0001-01-01T00:00:00</PROD_DELIVERY_NOT_IN_STOCK></STOCK></PRODUCT>
              <PRODUCT><GENERAL><PROD_NUM>BASELINE-002</PROD_NUM><LANGUAGE_ID>26</LANGUAGE_ID></GENERAL>
                <STOCK><STOCK_COUNT>0</STOCK_COUNT><PROD_DELIVERY_NOT_IN_STOCK>2026-10-15T00:00:00</PROD_DELIVERY_NOT_IN_STOCK></STOCK></PRODUCT>
            </ELEMENTS></PRODUCT_EXPORT>
            """);
        Assert.True(XNode.DeepEquals(expected, XDocument.Load(output).Root));
        Assert.Equal(new[] { "document.xml" }, Directory.GetFiles(Path.GetDirectoryName(output)!).Select(Path.GetFileName));
    }

    [Fact]
    public void MissingExclusionFileFailsWithoutWritingXml()
    {
        var output = Path.Combine(directory, "document.xml");
        Assert.Throws<FileNotFoundException>(() =>
            new XMLDataProvider(output, Path.Combine(directory, "missing.txt"))
                .GenerateInventoryFile(Array.Empty<InventoryService.DTOs.InventoryItemDTO>()));
        Assert.False(File.Exists(output));
    }

    [Fact]
    public void DeliveryDateUsesFirstSustainedPositiveStock()
    {
        var item = new InventoryItemCSV("TEST") { StockCount = -2 };
        item.Movements.Add(new InventoryMovement(new DateTime(2026, 10, 20), 5));
        item.Movements.Add(new InventoryMovement(new DateTime(2026, 10, 16), -3));
        item.Movements.Add(new InventoryMovement(new DateTime(2026, 10, 15), 3));
        Assert.Equal(new DateTime(2026, 10, 20), item.CalculateDeliveryDate());
    }

    public void Dispose() => Directory.Delete(directory, true);
}