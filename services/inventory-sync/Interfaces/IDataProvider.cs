using InventoryService.DTOs;

namespace InventoryService.Interfaces;

public interface IDataProvider
{
    /// <summary>
    ///     Used to instantiate a list of InventoryItems based on a file input.
    /// </summary>
    /// <returns>
    ///     A list of InventoryItems.
    /// </returns>
    public IEnumerable<InventoryItemDTO> GetInventoryItems();
    
    /// <summary>
    ///     Used to generate a file based on a list of InventoryItems.
    /// </summary>
    public void GenerateInventoryFile(IEnumerable<InventoryItemDTO> items);
}