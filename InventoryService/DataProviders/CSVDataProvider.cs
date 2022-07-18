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
        throw new NotImplementedException();
    }
}