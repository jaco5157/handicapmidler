// See https://aka.ms/new-console-template for more information

using System.Net.Http.Headers;
using InventoryService.DataProviders;
using InventoryService.DTOs;
using InventoryService.Interfaces;

// Instantiate empty list of InventoryItemDTO
IEnumerable<InventoryItemDTO> inventoryItems;

// Instantiante CSVDataProvider
IDataProvider dataProvider = new CSVDataProvider();

// Populate list with InventoryItemDTOs
inventoryItems = dataProvider.GetInventoryItems();

IDataProvider xmlWriter = new XMLDataProvider();
xmlWriter.GenerateInventoryFile(inventoryItems);