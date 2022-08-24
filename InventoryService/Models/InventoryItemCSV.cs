using System.Collections;

namespace InventoryService.Models;

public class InventoryItemCSV
{
    public InventoryItemCSV(string productNumber)
    {
        ProductNumber = productNumber;
    }

    public string ProductNumber { get; set; }
    public int StockCount { get; set; }
    
    public IEnumerable<InventoryMovement> Movements { get; set; }
    public int DeliveryTime { get; set; }
}