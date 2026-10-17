# Build, deployment, and rollback runbook

Commands use the current repository paths. The Phase 1 baseline retains historical paths for comparison.

## Product import

### Local verification

1. Copy `services/product-import/.env.example` to an untracked `.env` and keep `UPLOAD_ENABLED=false`.
2. Build and start the local service:

   ```sh
  cd services/product-import
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
- **Folder migration:** Follow [the existing-installation procedure](../services/product-import/DEPLOY_DIETPI.md#existing-installation-folder-migration) before the first pull containing the rename. Git does not move ignored state. Both Compose files retain project identity `product-import-service`; preserve any custom project-name override as well.
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

- Build with `.NET 8`: `dotnet build services/inventory-sync/InventoryService.csproj --configuration Release`.
- Test: `dotnet test services/inventory-sync/tests/InventoryService.Tests.csproj --configuration Release`.
- Invoke with explicit paths as shown in the [inventory README](../services/inventory-sync/README.md). Lowercase input filenames are retained; no repository working directory is inferred.
- Use the tracked [synthetic inventory fixtures](../reference/inventory/README.md), not live supplier snapshots. The tests copy them to a temporary directory. Formats:
  - `varer.LST`: product ID and product number, separated by `;`.
  - `lagerbehold.LST`: product ID and integer stock count, separated by `;`.
  - `lagerbevaeg.LST`: product ID, description, `dd-MM-yy` date, and integer movement amount.
  - `exclude.txt`: one excluded product number per line.
- Verify the result semantically: root `PRODUCT_EXPORT` with `type="PRODUCTS"`, one `PRODUCT` per non-excluded input, language ID 26, stock count, and calculated delivery date.

### Production deployment

- **Trigger:** `.github/workflows/inventory-workflow.yml` runs manually or daily at 16:00 UTC.
- **Destination:** The runner downloads supplier files into a temporary input directory and stages only generated `document.xml` in a separate upload directory. FTP still targets `images/ImportExport/Inventory/Updated/`, followed by the update-only import endpoint for `Inventory/Updated/document.xml`.
- **Required secrets:** `ftp_server`, `ftp_username`, `ftp_password`, `api_upload_endpoint`, `api_username`, and `api_password`.
- **Release procedure:** Merge a reviewed revision to the workflow's checked-out branch, manually dispatch the workflow, inspect all steps and the resulting import, and only then rely on the next scheduled run.

### Rollback

1. Disable the schedule or failing workflow before another run can publish data.
2. Revert to the previously successful workflow/service revision or check out `pre-restructure-2026-10-01`.
3. Dispatch manually using a fresh FTP download.
4. Validate the generated XML and DanDomain import result before restoring the schedule.

## Storefront assets

### Build and verification

The workflow runs `devatherock/minify-js:1.0.3` with `directory: storefront/assets`. Both nonempty `javascripts.min.js` and `styles.min.css` must exist before FTP runs. Generated files are ignored and must not be committed.

From the repository root, verify a temporary copy of the three deployment sources so local scratch files are not processed:

```sh
asset_check="$(mktemp -d)"
mkdir -p "$asset_check/storefront/assets"
cp storefront/assets/javascripts.js storefront/assets/styles.css \
  storefront/assets/handicapmidler.svg "$asset_check/storefront/assets/"
docker run --rm -v "$asset_check:/github/workspace" -w /github/workspace \
  -e INPUT_DIRECTORY=storefront/assets devatherock/minify-js:1.0.3
test -s "$asset_check/storefront/assets/javascripts.min.js"
test -s "$asset_check/storefront/assets/styles.min.css"
rm -r "$asset_check"
```

Compare output filenames first and hashes only when source content has not intentionally changed.

### Production deployment

- **Trigger:** Push to `main` changing `storefront/assets/**` or the deployment workflow, or `workflow_dispatch`.
- **Destination:** Remote FTP directory `assets/`.
- **Required secrets:** `ftp_server`, `ftp_username`, and `ftp_password`.
- **Verification:** Confirm the minification step reports both expected files, the FTP sync succeeds, and the storefront loads the updated assets without browser errors.

### Rollback

1. Revert the asset commit on `main`, or restore the known-good source from `pre-restructure-2026-10-01`.
2. Dispatch the deploy workflow.
3. Verify the remote destination remains `assets/` and smoke-test the storefront.

## Catalogue audit

- **Invocation/setup/tests:** See [catalogue audit](../tools/catalog-audit/README.md). Run `scraper.py` followed by `product-comparer.py`; both accept explicit paths and default to tool-local `generated/` files.
- **Inputs:** Mobilex catalogue pages, a DanDomain product export, Chrome/WebDriver, and Python packages pandas, selenium, and webdriver-manager.
- **Outputs:** Generated CSV reports.
- **Secrets:** None identified.
- **Verification:** Fixture comparison tests and an opt-in browser smoke; generated CSVs remain ignored.
- **Deployment:** None; this is a local operator tool.
- **Rollback:** Discard generated files and return to the last reviewed script revision.

## Referral reporting

- **Invocation/setup/tests:** See [referral reporting](../tools/reporting/referrals/README.md). Use `--input` for a semicolon-delimited CSV and optional `--output` for headless chart creation.
- **Inputs:** A CSV containing `REFERRER`; order exports may be sensitive.
- **Outputs:** Interactive seaborn/matplotlib chart or a saved chart. Keep real exports in ignored `private/` storage, not fixtures.
- **Secrets:** None identified.
- **Deployment:** None; local-only reporting utility.
- **Test:** Use a sanitized fixture and verify protocol/`www` removal, domain grouping, and chart creation.
- **Rollback:** Discard generated/local input data and return to the previous script revision.

## Manual image preparation

- **Invocation/setup/tests:** See [manual image preparation](../tools/image-prep/README.md). Run `bash tools/image-prep/compress.sh INPUT_DIR WORK_DIR OUTPUT_DIR`.
- **Requirements:** ImageMagick (`magick`) and Caesium CLI (`caesiumclt`).
- **Inputs/outputs:** Explicit directory arguments; originals are preserved and four JPEG variants are written to the output directory.
- **Safety:** Temporary working files are deleted unless `--keep-work` is supplied. Cleanup is restricted to the workspace created by the current run.
- **Deployment:** Result files are manually uploaded as required; no automated trigger is defined.
- **Rollback:** Restore original images from backup. For automated product imports, use the product-import service's Pillow implementation instead.

## CMS snippets

- **Sources:** `storefront/cms-snippets/active/subcats/` and `storefront/cms-snippets/active/templates/`; all 12 required files are listed in the [CMS manifest](CMS-MANIFEST.md).
- **Trigger/destination:** Manual installation into a verified DanDomain CMS location.
- **Required access:** DanDomain administrator credentials; do not store them in this repository.
- **Verification:** Confirm live usage and inspect the affected page at desktop and mobile widths.
- **Rollback:** Preserve the current live CMS content before replacement, then restore it if verification fails. Repository rollback uses Git history and `pre-restructure-2026-10-01`, not a permanent backup directory.
