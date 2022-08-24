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

public class DateComparer : IComparer<InventoryMovement>
{
    public int Compare(InventoryMovement x, InventoryMovement y)
    {
        if (ReferenceEquals(x, y)) return 0;
        if (ReferenceEquals(null, y)) return 1;
        if (ReferenceEquals(null, x)) return -1;
        return x.MovementDate.CompareTo(y.MovementDate);
    }
}