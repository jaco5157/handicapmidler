// See https://aka.ms/new-console-template for more information

using System.Net.Http.Headers;
using InventoryService.DataProviders;
using InventoryService.DTOs;
using InventoryService.Interfaces;

Console.WriteLine("Hello, World!");

IEnumerable<InventoryItemDTO> inventoryItems;
IDataProvider dataProvider = new CSVDataProvider();
inventoryItems = dataProvider.GetInventoryItems();

foreach (var inventoryItem in inventoryItems)
{
    Console.WriteLine("Product number: " + inventoryItem.ProductNumber + " has " + inventoryItem.StockCount + " items left");
}