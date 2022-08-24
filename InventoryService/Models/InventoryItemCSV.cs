using System.Collections;
using System.Collections.Immutable;
using System.Runtime.CompilerServices;

namespace InventoryService.Models;

public class InventoryItemCSV
{
    public InventoryItemCSV(string productNumber)
    {
        ProductNumber = productNumber;
        Movements = new List<InventoryMovement>();
    }

    public DateTime CalculateDeliveryDate()
    {
        Movements.Sort();
        var positiveStockDate = DateTime.MinValue;
        var stock = StockCount;
        foreach (var movement in Movements)
        {
            var oldStock = stock;
            stock += movement.Amount;
            if (stock <= 0) positiveStockDate = DateTime.MinValue;
            else if (oldStock <= 0) positiveStockDate = movement.MovementDate;
        }

        return positiveStockDate;
    }
    
    public string ProductNumber { get; set; }
    public int StockCount { get; set; }
    public List<InventoryMovement> Movements { get; set; }
    public int DeliveryTime { get; set; }
}