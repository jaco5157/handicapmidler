using InventoryService.Models;

namespace InventoryService.Interfaces;

public interface IDataProvider
{
    /// <summary>
    ///     Used to instantiate a list of InventoryItems based on a file input.
    /// </summary>
    /// <returns>
    ///     A list of InventoryItems.
    /// </returns>
    public IEnumerable<InventoryItem> GetInventoryItems();
}