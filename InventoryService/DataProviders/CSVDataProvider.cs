using InventoryService.Interfaces;
using InventoryService.DTOs;

namespace InventoryService.DataProviders;

public class CSVDataProvider: IDataProvider
{
    public IEnumerable<InventoryItemDTO> GetInventoryItems()
    {
        throw new NotImplementedException();
    }
}