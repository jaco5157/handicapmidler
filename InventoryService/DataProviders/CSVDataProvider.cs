using System.Collections;
using InventoryService.Interfaces;
using InventoryService.DTOs;
using InventoryService.Models;
using Microsoft.VisualBasic.FileIO;

namespace InventoryService.DataProviders;

public class CSVDataProvider: IDataProvider
{
    private string productsFile => Path.Combine("data", "varer.LST");
    private string inventoryFile => Path.Combine("data", "lagerbehold.LST");
    private string movementFile => Path.Combine("data", "lagerbevaeg.LST");
    public IEnumerable<InventoryItemDTO> GetInventoryItems()
    {
        var items = new Dictionary<string, InventoryItemCSV>();
        
        var parser = new TextFieldParser(productsFile);
        parser.TextFieldType = FieldType.Delimited;
        parser.SetDelimiters(";");

        // Instantiate products and add to temporary dictionary
        while (!parser.EndOfData)
        {
            string[] row = parser.ReadFields();
            
            if (row is not {Length: > 1}) continue;
            items.Add(row[0], new InventoryItemCSV(row[1]));
        }

        parser = new TextFieldParser(inventoryFile);
        parser.TextFieldType = FieldType.Delimited;
        parser.SetDelimiters(";");

        // Add current stock to each item
        while (!parser.EndOfData)
        {
            string[] row = parser.ReadFields();
            if (row is {Length: > 1} && items.ContainsKey(row[0]))
            {
                try
                {
                    items[row[0]].StockCount = int.Parse(row[1]);
                }
                catch
                {
                    // ignored
                }
            }
        }
        
        parser = new TextFieldParser(movementFile);
        parser.TextFieldType = FieldType.Delimited;
        parser.SetDelimiters(";");

        // Add all stock movements
        while (!parser.EndOfData)
        {
            string[] row = parser.ReadFields();
            if (row is {Length: > 1} && items.ContainsKey(row[0]))
            {
                if (items[row[0]].StockCount > 0) continue;
                try
                {
                    items[row[0]].Movements.Add(new InventoryMovement(DateTime.ParseExact(row[2],"dd-MM-yy",null), int.Parse(row[3])));
                }
                catch
                {
                    // ignored
                }
            }
        }

        // Convert to permanent DTO readable by other data providers
        return ConvertToDTO(items);
    }

    public void GenerateInventoryFile(IEnumerable<InventoryItemDTO> items)
    {
        throw new NotImplementedException();
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
                        item.Value.CalculateDeliveryDate())
                }));
        return result;
    }
}