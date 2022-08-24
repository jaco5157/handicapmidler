using System.Collections;
using System.Collections.Immutable;
using System.Runtime.CompilerServices;

namespace InventoryService.Models;

public class InventoryItemCSV
{
    public InventoryItemCSV(string productNumber)
    {
        ProductNumber = productNumber;
    }

    public DateTime CalculateDeliveryDate()
    {
        Movements.Sort();
        var positiveStockDate = DateTime.MinValue;
        var stock = StockCount;
        foreach (var movement in Movements)
        {
            stock += movement.Amount;
            positiveStockDate = stock <= 0 ? DateTime.MinValue : movement.MovementDate;
        }

        return positiveStockDate;
    }
    
    public string ProductNumber { get; set; }
    public int StockCount { get; set; }
    
    public List<InventoryMovement> Movements { get; set; }
    public int DeliveryTime { get; set; }
}