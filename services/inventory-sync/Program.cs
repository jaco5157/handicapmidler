using InventoryService;
using InventoryService.DataProviders;

var paths = InventoryPaths.Parse(args);
var inventoryItems = new CSVDataProvider(paths.InputDirectory).GetInventoryItems();
new XMLDataProvider(paths.OutputFile, paths.ExclusionFile).GenerateInventoryFile(inventoryItems);