using System.Xml.Linq;

namespace InventoryService.Models;

public class InventoryItemXML
{
    public InventoryItemXML(string productNumber, int stockCount, DateTime deliveryTime)
    {
        ProductNumber = productNumber;
        StockCount = stockCount;
        DeliveryTime = deliveryTime;
    }

    public string ProductNumber { get; set; }
    public int StockCount { get; set; }
    public DateTime DeliveryTime { get; set; }

    public XElement ToXML() => new("PRODUCT", 
        new XElement("GENERAL", 
            new XElement("PROD_NUM", this.ProductNumber), 
            new XElement("LANGUAGE_ID", 26)), 
        new XElement("STOCK",
            new XElement("STOCK_COUNT", this.StockCount), 
            new XElement("PROD_DELIVERY_NOT_IN_STOCK", 0)) //TODO: Calculate how many days until new delivery arrives 
        );
}