using InventoryService.Interfaces;
using InventoryService.DTOs;
using InventoryService.Models;

namespace InventoryService.DataProviders;

public class CSVDataProvider: IDataProvider
{
    public IEnumerable<InventoryItemDTO> GetInventoryItems()
    {
        throw new NotImplementedException();
    }

    public IEnumerable<InventoryItemDTO> ConvertToDTO(IEnumerable<InventoryItemCSV>? items)
    {
        var result = Enumerable.Empty<InventoryItemDTO>();
        if (items != null)
            result = items.Aggregate(result,
                (current, item) => current.Concat(new[]
                    {new InventoryItemDTO(item.ProductNumber, item.StockCount, item.DeliveryTime)}));

        return result;
    }
}