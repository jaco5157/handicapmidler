# Repository architecture

This repository is the monorepo for Handicapmidler.dk integrations, storefront assets, CMS snippets, and operational utilities. Production components, tools, reference data and verified CMS content use their restructured paths.

## System context

```mermaid
flowchart LR
    Supplier[Supplier websites] --> ProductImport[Product import service]
    Supplier --> CatalogAudit[Catalogue audit]
    InventoryFTP[Inventory FTP exports] --> InventorySync[Inventory sync]
    ProductImport --> ProductFTP[DanDomain product images and XML]
    ProductImport --> ProductAPI[DanDomain product import API]
    InventorySync --> InventoryFTPOut[DanDomain inventory XML folder]
    InventorySync --> InventoryAPI[DanDomain inventory import API]
    Assets[Storefront assets] --> AssetFTP[DanDomain assets folder]
    CMS[CMS snippets] -. manual installation .-> DanDomain[DanDomain CMS]
```

## Production components

### Product import

- **Current path:** `services/product-import`
- **Purpose:** Scrape a supplier product page, let an operator review the product, generate DanDomain product XML and image variants, and optionally upload/import them.
- **Runtime:** Python 3.12/FastAPI in Docker Compose; production host is a 64-bit DietPi/Raspberry Pi with private access through Tailscale Serve.
- **Invocation:** Operator-driven web UI. Deployment is a manual Git pull followed by a production Compose rebuild.
- **Inputs:** Supplier URL, operator-edited product fields, category export, environment configuration, and remote supplier images.
- **Outputs:** Persistent files under `data/`, four JPEG variants per enabled image, product XML, FTP uploads to `/images/products/` and `/images/ImportExport/Products/Updated/`, and a DanDomain import request.
- **Secrets:** `AUTH_PASSWORD_HASH`, FTP credentials, and DanDomain API credentials in a server-only `.env` file. Do not commit `.env`.
- **Behavioral boundary:** Dry-run is the default. Enabling upload also requires authentication.

### Inventory synchronization

- **Current path:** `services/inventory-sync`
- **Purpose:** Convert supplier stock and movement exports into DanDomain inventory XML and trigger an update-only import.
- **Runtime:** .NET 8 console application on a GitHub-hosted Ubuntu runner.
- **Invocation:** `.github/workflows/inventory-workflow.yml`, manually or every day at 16:00 UTC.
- **Inputs:** FTP files `VARER.LST`, `LAGERBEHOLD.LST`, and `LAGERBEVAEG.LST`, plus `exclude.txt`.
- **Outputs:** Only `document.xml` is staged in a separate runner-temporary upload directory and sent to `images/ImportExport/Inventory/Updated/`, followed by an update-only DanDomain import request.
- **Secrets:** GitHub Actions secrets `ftp_server`, `ftp_username`, `ftp_password`, `api_upload_endpoint`, `api_username`, and `api_password`.
- **Paths:** Required CLI arguments select the input directory, output XML and exclusion file. Paths are resolved once; providers do not infer repository locations.

### Storefront assets

- **Current path:** `storefront/assets`
- **Purpose:** Maintain the JavaScript, CSS and confirmed store logo automatically deployed to the webshop.
- **Runtime:** GitHub Actions using `devatherock/minify-js:1.0.3` and `SamKirkland/FTP-Deploy-Action@4.2.0`.
- **Invocation:** A push to `main` changing `storefront/assets/**` or its deployment workflow, or manual workflow dispatch.
- **Inputs:** `storefront/assets/javascripts.js`, `storefront/assets/styles.css` and `storefront/assets/handicapmidler.svg`.
- **Outputs:** `javascripts.min.js`, `styles.min.css` and the unchanged logo, synchronized to the remote `assets/` destination.
- **Secrets:** GitHub Actions secrets `ftp_server`, `ftp_username`, and `ftp_password`.

## Supported operational tools

### Catalogue audit

- **Current path:** `tools/catalog-audit`
- **Purpose:** Scrape Mobilex catalogue pages and report products missing from a DanDomain product export. This is a catalogue-gap audit, not the single-product import workflow.
- **Runtime/invocation:** Manually executed Python scripts using Selenium, Chrome, pandas, and webdriver-manager.
- **Inputs:** Default or CLI-selected Mobilex category starting URLs and an exported product XML file.
- **Outputs:** Generated Mobilex and missing-product CSV reports.
- **Secrets:** None identified.
- **Paths:** Default outputs and comparison inputs are relative to the tool's ignored `generated/` directory; CLI flags override them. Dependencies are pinned locally.

### Referral reporting

- **Current path:** `tools/reporting/referrals`
- **Purpose:** Aggregate order referrer domains and display a chart.
- **Runtime/invocation:** Manually executed Python script using pandas, matplotlib, and seaborn.
- **Inputs:** Semicolon-delimited `referrals.csv` containing at least `REFERRER`.
- **Outputs:** Interactive bar chart or a CLI-selected image file.
- **Secrets:** None identified, but order exports may contain sensitive production data and must not be committed.
- **Data:** Input is required via `--input`; only synthetic fixtures are tracked. Real exports belong in ignored `private/` storage.

### Manual image preparation

- **Current path:** `tools/image-prep`
- **Purpose:** Manually trim images, convert them to JPEG, and make the four webshop image variants.
- **Runtime/invocation:** Manual Bash script requiring ImageMagick's `magick` command and Caesium CLI's `caesiumclt` command.
- **Inputs:** Explicit input, work and output directory arguments.
- **Outputs:** JPEG variants named `name-p.jpg`, `name.jpg`, `name-r.jpg`, and `name-t.jpg` in the selected output directory.
- **Secrets:** None.
- **Safety:** Only the per-run temporary workspace is deleted; `--keep-work` retains it. Original inputs are preserved. The Pillow implementation in product import is authoritative for automated imports; continued use of this manual tool remains unconfirmed.

## Reference and manually managed content

### CMS snippets

- **Current path:** `storefront/cms-snippets/active`, grouped into `subcats/` and `templates/`.
- **Review path:** `storefront/cms-snippets/review` for any future required snippets awaiting live-location verification.
- **Purpose:** HTML, CSS, and JavaScript manually copied into DanDomain CMS locations.
- **Invocation:** Manual review and installation in DanDomain; no automated deployment exists.
- **Inputs/outputs:** Repository snippets are manually copied to their verified DanDomain page, template, or component location.
- **Secrets:** DanDomain administrator access, managed outside this repository.
- **Control:** [CMS manifest](CMS-MANIFEST.md) records all 12 required files. Live-location verification is recorded in the [Phase 1 exit record](PHASE-1-BASELINE.md#phase-1-exit-record). Retain all files; later removal requires explicit approval and separate review.

### Brand source

- **Current path:** `graphics/handicapmidler.svg`
- **Deployment copy:** `storefront/assets/handicapmidler.svg`.
- **Purpose:** Confirmed current store logo; the original and deployment copy are byte-identical.
- **Deployment:** The existing asset workflow publishes the copy to remote `assets/`; no current logo URL is changed.

### Reference exports and inventory samples

- **Current paths:** [DanDomain examples](../reference/dandomain/README.md) and [inventory fixtures](../reference/inventory/README.md).
- **Purpose:** Preserve product XML contract references and small synthetic inventory inputs.
- **Classification:** XML examples are unchanged, unsanitized production-derived catalogue data with documented Git source dates; actual export dates are unknown. Inventory fixtures contain only synthetic product numbers and controlled stock/movement values.
- **Control:** Tests consume the inventory fixtures. Supplier snapshots and product CSV exports are not tracked; root `inventory/`, service-local data and generated reference XML are ignored.
