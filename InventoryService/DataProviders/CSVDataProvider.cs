using System.Collections;
using InventoryService.Interfaces;
using InventoryService.DTOs;
using InventoryService.Models;
using Microsoft.VisualBasic.FileIO;

namespace InventoryService.DataProviders;

public class CSVDataProvider: IDataProvider
{
    private string productsFile => Path.Combine("data", "products.json");
    private string inventoryFile => Path.Combine("data", "products.json");
    public IEnumerable<InventoryItemDTO> GetInventoryItems()
    {
        var items = new Dictionary<string, InventoryItemCSV>();
        
        var parser = new TextFieldParser(productsFile);
        parser.TextFieldType = FieldType.Delimited;
        parser.SetDelimiters(";");

        while (!parser.EndOfData)
        {
            string[] row = parser.ReadFields();
            if (row != null && row.Length != 0)
            {
                items.Add(row[0], new InventoryItemCSV(row[1]));
            }
        }
        
        parser = new TextFieldParser(inventoryFile);
        parser.TextFieldType = FieldType.Delimited;
        parser.SetDelimiters(";");
        
        while (!parser.EndOfData)
        {
            string[] row = parser.ReadFields();
            if (row != null && row.Length != 0)
            {
                items[row[0]].StockCount = Int32.Parse(row[1]);
            }
        }
        
        return ConvertToDTO(items);
    }

    public IEnumerable<InventoryItemDTO> ConvertToDTO(Dictionary<string, InventoryItemCSV>? items)
    {
        var result = Enumerable.Empty<InventoryItemDTO>();
        if (items != null)
            result = items.Aggregate(result,
                (current,
                    item) => current.Concat(new[]
                {
                    new InventoryItemDTO(item.Value.ProductNumber,
                        item.Value.StockCount,
                        item.Value.DeliveryTime)
                }));
        return result;
    }
}