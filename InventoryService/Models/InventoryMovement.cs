namespace InventoryService.Models;

public class InventoryMovement
{
    public InventoryMovement(DateTime movementDate, int amount)
    {
        MovementDate = movementDate;
        Amount = amount;
    }

    public DateTime MovementDate { get; set; }
    public int Amount { get; set; }
}