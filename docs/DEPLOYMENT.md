# Build, deployment, and rollback runbook

Commands in this document use the pre-restructure paths. Update them in the same commit as each Phase 2 or later move.

## Product import

### Local verification

1. Copy `services/product-import-service/.env.example` to an untracked `.env` and keep `UPLOAD_ENABLED=false`.
2. Build and start the local service:

   ```sh
   cd services/product-import-service
   docker compose up --build --detach
   ```

3. Run the complete tests in the application image while neutralizing developer `.env` authentication/upload values:

   ```sh
   docker compose run --rm --no-deps \
     -e AUTH_ENABLED=false -e AUTH_USERNAME= -e AUTH_PASSWORD_HASH= \
     -e UPLOAD_ENABLED=false -v "$PWD:/app" \
     product-import-service python -m pytest -q
   ```

4. Check `http://127.0.0.1:8765/health`; the expected status is HTTP 200 with `{"status":"ok"}`.
5. Open `http://127.0.0.1:8765/`, fetch categories, and complete a dry-run preview. Verify that files remain under the service-local `data/` directory and no remote upload occurs.

### Production deployment

- **Trigger:** Manual update on the DietPi host; there is no product-import GitHub Actions deployment.
- **Destination:** Docker Compose on the DietPi host, bound to `127.0.0.1:8000` and exposed privately through Tailscale Serve.
- **Command:** From the service directory, pull the reviewed revision and run `docker compose -f docker-compose.prod.yml up -d --build`.
- **Persistent state:** Back up server-only `.env` and `data/` before deployment. The bind-mounted `data/` directory contains categories, generated XML, original images, and compressed images.
- **Required secrets:** `AUTH_USERNAME`, `AUTH_PASSWORD_HASH`, `FTP_HOST`, `FTP_USERNAME`, `FTP_PASSWORD`, `UPLOAD_ENDPOINT`, `API_USERNAME`, and `API_PASSWORD`. Keep uploads disabled until all upload and authentication settings are present.

### Production verification

1. Confirm Compose reports the service healthy.
2. Check `/health` locally on the host.
3. Confirm the UI loads through private Tailscale access and requires authentication.
4. Fetch categories and run a dry-run product first.
5. For an approved live smoke test, verify image files, the uniquely named product XML, and the structured DanDomain import result.

### Rollback

1. Disable uploads in `.env` if the current version can start safely.
2. Check out the previously deployed commit or the pre-migration tag `pre-restructure-2026-10-01`.
3. Restore `.env` and `data/` from the pre-deployment backup if state was damaged.
4. Rebuild with the production Compose file and repeat the health/UI checks.

## Inventory synchronization

### Build and controlled verification

- Build with `.NET 8`: `dotnet build scripts/InventoryService/InventoryService.csproj --configuration Release`.
- Run from the repository root. The current implementation expects lowercase input names under root `data/` and separately expects `InventoryService/exclude.txt` relative to the process working directory.
- Do not test with live supplier snapshots in Git. Use temporary controlled files with these formats:
  - `varer.LST`: product ID and product number, separated by `;`.
  - `lagerbehold.LST`: product ID and integer stock count, separated by `;`.
  - `lagerbevaeg.LST`: product ID, description, `dd-MM-yy` date, and integer movement amount.
  - `exclude.txt`: one excluded product number per line.
- Verify the result semantically: root `PRODUCT_EXPORT` with `type="PRODUCTS"`, one `PRODUCT` per non-excluded input, language ID 26, stock count, and calculated delivery date.

### Production deployment

- **Trigger:** `.github/workflows/inventory-workflow.yml` runs manually or daily at 16:00 UTC.
- **Destination:** The runner currently uploads all root `data/` content to `images/ImportExport/Inventory/Updated/` and then calls the update-only DanDomain import endpoint for `Inventory/Updated/document.xml`.
- **Required secrets:** `ftp_server`, `ftp_username`, `ftp_password`, `api_upload_endpoint`, `api_username`, and `api_password`.
- **Release procedure:** Merge a reviewed revision to the workflow's checked-out branch, manually dispatch the workflow, inspect all steps and the resulting import, and only then rely on the next scheduled run.

### Rollback

1. Disable the schedule or failing workflow before another run can publish data.
2. Revert to the previously successful workflow/service revision or check out `pre-restructure-2026-10-01`.
3. Dispatch manually using a fresh FTP download.
4. Validate the generated XML and DanDomain import result before restoring the schedule.

## Storefront assets

### Build and verification

The workflow runs `devatherock/minify-js:1.0.3` with `directory: deploy`. It creates `deploy/javascripts.min.js` and `deploy/styles.min.css`. Generated files are workflow artifacts only and should not be committed.

For local reproduction, use the same container image against a temporary copy of `deploy/`; do not let a baseline run alter tracked sources. Compare output filenames first and hashes only when source content has not intentionally changed.

### Production deployment

- **Trigger:** Push to `main` changing `deploy/**`, or `workflow_dispatch`.
- **Destination:** Remote FTP directory `assets/`.
- **Required secrets:** `ftp_server`, `ftp_username`, and `ftp_password`.
- **Verification:** Confirm the minification step reports both expected files, the FTP sync succeeds, and the storefront loads the updated assets without browser errors.

### Rollback

1. Revert the asset commit on `main`, or restore the known-good source from `pre-restructure-2026-10-01`.
2. Dispatch the deploy workflow.
3. Verify the remote destination remains `assets/` and smoke-test the storefront.

## Catalogue audit

- **Current invocation:** Manual Python execution of `scripts/product-scraper/scraper.py` followed by `scripts/product-scraper/product-comparer.py`.
- **Inputs:** Mobilex catalogue pages, a DanDomain product export, Chrome/WebDriver, and Python packages pandas, selenium, and webdriver-manager.
- **Outputs:** Generated CSV reports.
- **Secrets:** None identified.
- **Current support status:** Blocked by hard-coded `productService/generated` paths and unpinned dependencies. Do not present current output as a reproducible baseline until Phase 3 repairs it.
- **Deployment:** None; this is a local operator tool.
- **Rollback:** Discard generated files and return to the last reviewed script revision.

## Referral reporting

- **Current invocation:** From `scripts/`, run `python statistics/referrals.py` with a semicolon-delimited `statistics/referrals.csv`. The fixed relative path does not resolve when the script is launched from the repository root or its own directory.
- **Inputs:** A CSV containing `REFERRER`; order exports may be sensitive.
- **Outputs:** Interactive seaborn/matplotlib chart.
- **Secrets:** None identified.
- **Deployment:** None; local-only reporting utility.
- **Test:** Use a sanitized fixture and verify protocol/`www` removal, domain grouping, and chart creation.
- **Rollback:** Discard generated/local input data and return to the previous script revision.

## Manual image preparation

- **Invocation:** Run root `compress.sh` only from a dedicated working directory containing `Compress/`.
- **Requirements:** ImageMagick (`magick`) and Caesium CLI (`caesiumclt`).
- **Inputs/outputs:** Reads `./Compress/`; writes variants under `./Compressed/`.
- **Safety:** The final command deletes all content under `./Compress/`. Back up source images and confirm the current directory before running.
- **Deployment:** Result files are manually uploaded as required; no automated trigger is defined.
- **Rollback:** Restore original images from backup. For automated product imports, use the product-import service's Pillow implementation instead.

## CMS snippets

- **Trigger/destination:** Manual installation into a verified DanDomain CMS location.
- **Required access:** DanDomain administrator credentials; do not store them in this repository.
- **Verification:** Record the exact live location, owner, and date in `docs/CMS-MANIFEST.md`; inspect the affected page at desktop and mobile widths.
- **Rollback:** Preserve the current live CMS content before replacement, then restore it if verification fails. Repository rollback uses Git history and `pre-restructure-2026-10-01`, not a permanent backup directory.
