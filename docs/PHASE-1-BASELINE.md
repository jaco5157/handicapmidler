# Phase 1 baseline

Captured on 2026-10-01 before any repository paths were moved.

## Source control

- Branch: `feature/repository-restructure`
- Baseline commit: `7606215` (`Merge pull request #62 from jaco5157/feature/product-import-service`)
- Annotated and published tag: `pre-restructure-2026-10-01`
- Pre-existing untracked content at capture time: `spec/` (contains the restructuring plan and is intentionally not part of the tagged baseline)

The tag points to the unchanged pre-migration commit. Documentation created during Phase 1 is therefore recoverable from the feature branch while the tag remains an exact rollback point for production behavior.

## Product import

### Test suite

The complete suite was run in the existing Compose application image with the repository bind-mounted and local authentication/upload values neutralized.

- Result: **60 passed, 2 warnings**
- Duration: **0.58 seconds**
- Runtime: container Python 3.12
- Warnings: Starlette deprecations for the AnyIO `BlockingPortal` alias and legacy `TemplateResponse` argument order
- Failures: **0**

### Service health

The existing local Compose service was running at `127.0.0.1:8765`.

- `GET /health`: HTTP **200**
- Body: `{"status":"ok"}`
- UI: Loaded successfully in the browser
- Upload behavior: Local configuration was not used during tests; test execution explicitly forced `UPLOAD_ENABLED=false`

## Inventory synchronization

### Build

`dotnet build scripts/InventoryService/InventoryService.csproj --configuration Release` was run with the .NET 8 SDK.

- Result: **Succeeded**
- Errors: **0**
- Warnings: **5**
  - One uninitialized non-nullable `ProductNumber` property warning
  - One possible null source passed to `Enumerable.ToArray`
  - Three possible null `ReadFields()` assignments

### Representative XML

The executable was run from a temporary working directory against controlled fixtures. No repository inventory snapshots or root `data/` files were changed.

Fixture behavior:

- `BASELINE-001`: stock 7 and no movements
- `BASELINE-002`: stock 0 and a +5 movement dated 2026-10-15
- `3020S8`: stock 99 but excluded by the existing exclusion list

Observed output:

```xml
<?xml version="1.0" encoding="utf-8"?>
<PRODUCT_EXPORT type="PRODUCTS">
  <ELEMENTS>
    <PRODUCT>
      <GENERAL>
        <PROD_NUM>BASELINE-001</PROD_NUM>
        <LANGUAGE_ID>26</LANGUAGE_ID>
      </GENERAL>
      <STOCK>
        <STOCK_COUNT>7</STOCK_COUNT>
        <PROD_DELIVERY_NOT_IN_STOCK>0001-01-01T00:00:00</PROD_DELIVERY_NOT_IN_STOCK>
      </STOCK>
    </PRODUCT>
    <PRODUCT>
      <GENERAL>
        <PROD_NUM>BASELINE-002</PROD_NUM>
        <LANGUAGE_ID>26</LANGUAGE_ID>
      </GENERAL>
      <STOCK>
        <STOCK_COUNT>0</STOCK_COUNT>
        <PROD_DELIVERY_NOT_IN_STOCK>2026-10-15T00:00:00</PROD_DELIVERY_NOT_IN_STOCK>
      </STOCK>
    </PRODUCT>
  </ELEMENTS>
</PRODUCT_EXPORT>
```

- Product count: **2**
- Exclusion behavior: `3020S8` absent as expected
- SHA-256 of the generated baseline file: `ce8a2214877f9ffe46ed6224d824b13040030bb74778f9d0c16b36aa30ca6415`

The checksum is a byte-level diagnostic for the current implementation. Phase 2 verification must primarily compare XML semantics because formatting, encoding declarations, or element serialization can change without changing the import contract.

## Storefront assets

The exact workflow image `devatherock/minify-js:1.0.3` was run against a temporary copy of `deploy/` with the workflow's `directory: deploy` setting.

| Source | Generated name | SHA-256 |
| --- | --- | --- |
| `deploy/javascripts.js` | `javascripts.min.js` | `ee5f49b689b8d3ea9b274ca78ad8e6aeaca7d5669ad6c3adfc217c534444a0ed` |
| `deploy/styles.css` | `styles.min.css` | `df8c9e37cc764e1fd26067e297fa669fc9504e2041a3002e7985d3f32fef8e33` |

The remote workflow destination is `assets/`. Phase 2 must preserve both generated names and that destination.

## Known limitations carried into later phases

- Inventory input/output paths depend on the current working directory; the exclusion file uses a different hard-coded relative path.
- Inventory workflow currently uploads every downloaded file in `data/`, not only generated XML.
- Catalogue-audit scripts point to nonexistent `productService/generated` paths and have no pinned dependency set.
- Referral reporting uses a fixed relative input path.
- The manual image script deletes all content under `./Compress/` after processing.
- Every tracked file under `static/` lacks a verified live CMS mapping. All are quarantined administratively in the CMS manifest until manual verification.
- Component owners are not documented. They are marked **Unassigned** rather than inferred.

## Phase 1 exit record

- [x] Feature branch confirmed
- [x] Pre-migration tag created and pushed
- [x] Product-import tests recorded
- [x] Product-import health check recorded
- [x] Inventory build recorded
- [x] Representative inventory XML recorded
- [x] Storefront minified filenames and hashes recorded
- [x] Root component index updated
- [x] Architecture and deployment runbooks added
- [x] All tracked files under `static/` entered in the CMS manifest
- [ ] Operational owners assigned
- [ ] CMS live locations manually verified

The final two items require business/CMS knowledge and remain explicit follow-up work; no production location or owner was guessed during the repository audit.
