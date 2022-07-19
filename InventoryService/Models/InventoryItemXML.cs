namespace InventoryService.Models;

public class InventoryItemXML
{
    public InventoryItemXML(string productNumber, int stockCount, int deliveryTime)
    {
        ProductNumber = productNumber;
        StockCount = stockCount;
        DeliveryTime = deliveryTime;
    }

    public string ProductNumber { get; set; }
    public int StockCount { get; set; }
    public int DeliveryTime { get; set; }
}