namespace InventoryService.Models;

public class InventoryItemCSV
{
    public string ProductNumber { get; set; }
    public string StockCount { get; set; }
    public string? DeliveryTime { get; set; }
}