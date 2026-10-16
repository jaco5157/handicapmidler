# Inventory Sync

.NET 8 scheduled stock integration. The assembly and namespace remain `InventoryService`; only the repository location changes.

## Build and test

From the repository root:

```sh
dotnet build services/inventory-sync/InventoryService.csproj --configuration Release
dotnet test services/inventory-sync/tests/InventoryService.Tests.csproj --configuration Release
```

Tests copy the [synthetic reference fixtures](../../reference/inventory/README.md) into a temporary directory and compare XML semantics with the Phase 1 baseline, including exclusions and delivery dates. The fixture README also provides a local generation command.

## Run

```sh
dotnet run --project services/inventory-sync/InventoryService.csproj --configuration Release -- \
  --input-dir /absolute/path/to/supplier-input \
  --output-file /absolute/path/to/upload/document.xml \
  --exclude-file "$PWD/services/inventory-sync/exclude.txt"
```

All three arguments are required. Relative arguments resolve against the invocation directory; absolute paths work from any directory. The output parent is created automatically; a missing exclusion file fails without generating XML.

Input files are semicolon-delimited:

| Filename | Columns |
| --- | --- |
| `varer.LST` | Product ID; product number |
| `lagerbehold.LST` | Product ID; integer stock |
| `lagerbevaeg.LST` | Product ID; description; `dd-MM-yy` date; integer movement |

`exclude.txt` contains one product number per line. Keep downloaded supplier snapshots out of Git.

## Deployment

[Inventory workflow](../../.github/workflows/inventory-workflow.yml) runs daily at 16:00 UTC or by manual dispatch. It tests first, downloads into a runner-temporary input directory, generates XML in a separate upload directory, and uploads only `document.xml` to the unchanged `images/ImportExport/Inventory/Updated/` destination before calling the update-only import endpoint.

Secrets and release/rollback checks are in the [deployment runbook](../../docs/DEPLOYMENT.md#inventory-synchronization). Manually dispatch and inspect the import before relying on the schedule.

For a container invocation, build with `docker build -t inventory-sync:local services/inventory-sync`, mount input/output directories, and pass the same three arguments after the image name. The published exclusion list is `/app/exclude.txt`.