# Synthetic inventory fixtures

Created 2026-10-16 as synthetic test inputs, not supplier snapshots. All product numbers are synthetic; the excluded item uses `BASELINE-EXCLUDED` instead of a real product number.

| File | Semicolon-delimited columns |
| --- | --- |
| `varer.LST` | Product ID; synthetic product number |
| `lagerbehold.LST` | Product ID; integer stock count |
| `lagerbevaeg.LST` | Product ID; description; `dd-MM-yy` date; integer movement |
| `exclude.txt` | One excluded synthetic product number per line |

The three products cover stock 7 without movements, stock 0 with a +5 movement on 2026-10-15, and stock 99 excluded from the output. The [inventory tests](../../services/inventory-sync/tests/InventoryTests.cs) consume these files and verify generated XML semantics, including stock counts, exclusions and delivery dates.

From the repository root, generate local XML without an upload:

```sh
dotnet run --project services/inventory-sync/InventoryService.csproj --configuration Release -- \
  --input-dir "$PWD/reference/inventory" \
  --output-file "$PWD/services/inventory-sync/data/reference-document.xml" \
  --exclude-file "$PWD/reference/inventory/exclude.txt"
```

Keep supplier snapshots and real product exports in ignored local storage such as root `inventory/`. Generated XML is ignored here and under `services/inventory-sync/data/`; do not add live data to these fixtures.