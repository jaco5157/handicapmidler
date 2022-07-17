namespace InventoryService.Models;

public class InventoryItem
{
    public InventoryItem(string productNumber, string stockCount, string? deliveryTime)
    {
        ProductNumber = productNumber;
        StockCount = stockCount;
        DeliveryTime = deliveryTime;
    }

    public string ProductNumber { get; set; }
    public string StockCount { get; set; }
    public string? DeliveryTime { get; set; }
}