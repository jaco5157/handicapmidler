namespace InventoryService.Models;

public class InventoryItemCSV
{
    public string ProductNumber { get; set; }
    
    public int ItideProductNumber { get; set; }
    public int StockCount { get; set; }
    public int? DeliveryTime { get; set; }
}