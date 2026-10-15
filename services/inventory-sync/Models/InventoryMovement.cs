namespace InventoryService.Models;

public class InventoryMovement : IComparable<InventoryMovement>
{
    public InventoryMovement(DateTime movementDate, int amount)
    {
        MovementDate = movementDate;
        Amount = amount;
    }

    public DateTime MovementDate { get; set; }
    public int Amount { get; set; }

    public int CompareTo(InventoryMovement? other)
    {
        if (ReferenceEquals(this, other)) return 0;
        if (ReferenceEquals(null, other)) return 1;
        return MovementDate.CompareTo(other.MovementDate);
    }
}