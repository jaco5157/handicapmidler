using System.ComponentModel;
using System.Xml.Linq;
using InventoryService.DTOs;
using InventoryService.Interfaces;
using InventoryService.Models;

namespace InventoryService.DataProviders;

public class XMLDataProvider: IDataProvider
{
    private readonly string outputFile;
    private readonly string exclusionFile;

    public XMLDataProvider(string outputFile, string exclusionFile)
    {
        this.outputFile = Path.GetFullPath(outputFile);
        this.exclusionFile = Path.GetFullPath(exclusionFile);
    }

    public IEnumerable<InventoryItemDTO> GetInventoryItems()
    {
        throw new NotImplementedException();
    }

    public void GenerateInventoryFile(IEnumerable<InventoryItemDTO> items)
    {
        var inventoryItemDtos = items as InventoryItemDTO[] ?? items.ToArray();
        var excludedProductNumbers = File.ReadAllLines(exclusionFile);


        var elements = new XElement("ELEMENTS");
        elements.Add(
            from item in inventoryItemDtos
            where !excludedProductNumbers.Contains(item.ProductNumber)
            select item.ToXML()
            );
        
        var doc = new XDocument(
            new XElement( "PRODUCT_EXPORT", 
                new XAttribute("type", "PRODUCTS"), 
                elements)
            );

        Directory.CreateDirectory(Path.GetDirectoryName(outputFile)!);
        doc.Save(outputFile);
    }
    
    public IEnumerable<InventoryItemDTO> ConvertToDTO(IEnumerable<InventoryItemXML> items)
    {
        var result = Enumerable.Empty<InventoryItemDTO>();
        if (items != null)
            result = items.Aggregate(result,
                (current,
                    item) => current.Concat(new[]
                {
                    new InventoryItemDTO(item.ProductNumber,
                        item.StockCount,
                        item.DeliveryTime)
                }));
        return result;
    }
}