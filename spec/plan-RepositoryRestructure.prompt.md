# Plan: Restructure Webshop Monorepo

Keep one repository, but reorganize it around clear deployment and ownership boundaries. Execute the migration as incremental, reversible commits while preserving current production behavior.

## Readiness review

| Phase | Status |
| --- | --- |
| 1 | Complete: baseline and CMS inventory recorded. |
| 2 | Implemented: steps 6-8 and local verification pass. Production workflow dispatches and DietPi host migration remain pending. |
| 3 | Implemented: steps 9-11, pinned dependencies, explicit paths, data-safety fixes and focused tests are complete. |
| 4 | Implemented: XML examples relocated and classified, synthetic inventory fixtures tested, supplier snapshots untracked, and all 12 verified CMS files moved unchanged. The confirmed logo copy matches the original. |
| 5 | Move-specific ignore rules and active documentation updated. Final integration and cleanup remain pending, including production verification. |

Verified 2026-10-15: product import **60 passed, 2 warnings** before and after relocation, in Docker and the recreated native environment; Compose build/start, `/health` **HTTP 200**, UI, dry-run XML/image preview and the relocated persistent mount pass. Inventory build and **8 tests** pass, including semantic baseline XML, exclusions and delivery dates. Both minified filenames and SHA-256 hashes match the October 1 baseline. Catalogue audit **6 tests** (including a live browser smoke), reporting **4 tests**, and image preparation **3 tests** plus real ImageMagick/Caesium processing pass. Workflow syntax and ignore checks pass. No production uploads or workflow dispatches were performed.

Phase 4 implementation (2026-10-16):

- **Step 12:** Both examples are retained byte-for-byte under `reference/dandomain` with descriptive names. The local README records first-tracked Git source dates, unknown actual export dates, purpose and an explicit unsanitized production-derived catalogue-data classification.
- **Step 13:** `reference/inventory` contains three tiny synthetic LST inputs and a synthetic exclusion list consumed by the semantic baseline test. The three supplier LST snapshots and product CSV export remain locally in ignored root `inventory/`, no longer tracked.
- **Step 14:** All 12 required CMS files are retained byte-for-byte under `storefront/cms-snippets/active`, preserving subcategory/template groupings, filenames and required status. Manual live-location verification remains recorded in the [Phase 1 exit record](../docs/PHASE-1-BASELINE.md#phase-1-exit-record); the CMS manifest links to the current sources.
- **Step 15:** The owner confirms `graphics/handicapmidler.svg` is the current store logo. An unchanged copy is retained at `storefront/assets/handicapmidler.svg` for the existing asset deployment; the original remains in `graphics/`.

Phase 4 verification: inventory Release build and **8 tests** pass; controlled CLI generation produces valid XML with two products. Both relocated XML examples parse. All 12 CMS snippets, both XML examples and the logo copy pass byte-identity checks. Documentation links, ignore rules and whitespace checks pass; the four untracked inventory data files remain unchanged locally. No commits, workflow dispatches or production changes were performed.

## Target organization

- **services**
  - **product-import** — FastAPI product import application
  - **inventory-sync** — scheduled .NET inventory integration
- **storefront**
   - **assets** — automatically deployed CSS, JavaScript and store logo
  - **cms-snippets/active** — verified, manually installed DanDomain snippets
  - **cms-snippets/review** — quarantined content with uncertain usage
- **tools**
  - **catalog-audit** — repaired product scraper/comparer
  - **reporting/referrals** — statistics utility
  - **image-prep** — manual image-processing utility
- **reference**
  - **dandomain** — XML examples
  - **inventory** — small, sanitized inventory fixtures
- **docs**
  - Architecture, deployment, CMS manifest and operational documentation

## Phase 1 — Baseline and documentation

1. Create a feature branch and pre-migration Git tag.
2. Record baseline results:
   - Product-import tests and health check
   - Inventory build and representative generated XML
   - Storefront minified output names
3. Replace the outdated description in README.md with an index of all active components.
4. Add architecture and deployment documentation covering:
   - Purpose
   - Runtime or invocation method
   - Inputs and outputs
   - Deployment trigger and destination
   - Required secrets
   - Test and rollback procedure
5. Inventory every file under static. Record purpose and status.
   - Mark all remaining CMS source files as `Active` (required) in the manifest and retain them throughout migration.

## Phase 2 — Establish production boundaries

6. Move deploy into the storefront asset area.
   - Update all path filters, minification paths, verification paths and FTP source paths in deploy-workflow.yml.
   - Preserve the remote `assets/` destination and generated filenames.
   - Fail verification unless both `javascripts.min.js` and `styles.min.css` exist; the current warning-only check is not a release gate.
   - Validate through `workflow_dispatch`.

7. Move scripts/InventoryService into the services area as **inventory-sync**. This can run in parallel with step 6.
   - Update inventory-workflow.yml.
   - Remove working-directory assumptions from `CSVDataProvider`.
   - Make input, output and exclusion-file locations explicit.
   - Remove the hard-coded exclusion path in `XMLDataProvider.cs`.
   - Stage and upload only the generated import XML rather than all downloaded source files.
   - Add focused tests for path resolution and XML generation.

8. Shorten services/product-import-service to **product-import**. This can run in parallel with steps 6–7.
   - Update commands in its README.
   - Update the DietPi guide, Docker Compose references and documentation.
   - Back up and explicitly transfer the ignored `.env` and `data/` on existing installations; Git does not relocate them with tracked files.
   - Preserve the existing Compose project identity or explicitly stop the old stack before starting the renamed project, avoiding duplicate stacks and port conflicts.
   - Preserve ports, environment names, volumes, authentication and deployment behavior.
   - Require identical or better test results before and after the move.

## Phase 3 — Convert scripts into supported tools

9. Move scripts/product-scraper into **catalog-audit**.
   - Preserve its catalogue-gap purpose, which differs from single-product importing.
   - Replace broken `productService/generated` paths in scraper.py and product-comparer.py.
   - Resolve paths relative to the tool or through command-line arguments.
   - Add pinned dependencies, usage documentation and local comparison tests.
   - Keep generated CSV files ignored.

10. Move scripts/statistics into the reporting tools area.
    - Make the input CSV configurable instead of relying on the current relative path in referrals.py.
    - Document required columns and dependencies.
    - Retain only sanitized fixture data.

11. Move compress.sh into the image-preparation tool area.
    - Document ImageMagick and Caesium requirements.
    - Make input, working and output directories explicit.
    - Warn about destructive cleanup.
    - Treat the product-import service’s Pillow implementation as authoritative for automated imports.
    - Remove this manual tool later if no continuing use is confirmed.

Steps 9–11 can proceed in parallel after the baseline is captured.

## Phase 4 — Reference data and CMS quarantine

12. Move export.xml and export-sample-all-fields.xml into the DanDomain reference area.
    - Give them descriptive names.
    - Record source date, purpose and production-data status.
    - Update all documentation references.

13. Review inventory.
    - Preserve only small, sanitized inputs useful for testing.
    - Ignore current supplier snapshots and generated output.
    - Do not treat live FTP downloads as source code.

14. Retain every remaining CMS source file under static as required content.
   - Preserve the subcategory and reusable-template groupings during relocation.
   - Move files to `storefront/cms-snippets/active` only after confirming their live DanDomain usage.
   - Place any still-unverified files in `storefront/cms-snippets/review` without changing their required status.
   - Do not delete required files during migration. Any later removal needs explicit user approval and a separate reviewed commit.
    - Use the pre-migration tag and Git history instead of creating a permanent archive folder.

15. Retain an unchanged copy of the confirmed store logo in `storefront/assets/handicapmidler.svg`, preserving the original in `graphics/`.

## Phase 5 — Integration and cleanup

16. Update .gitignore for:
    - Build output
    - Service-local data
    - Generated reports and catalogue results
    - Python environments
    - Secrets
    - OS metadata
    - Tool working directories
   - Apply rules needed for each component in its move, rather than waiting for final cleanup. Ignore rules do not untrack existing data; review tracked supplier snapshots and reporting exports separately.

17. Search for all obsolete path references, especially:

    - The original deployment directory
    - The original InventoryService location
    - The original product-import-service location
    - `productService/generated`
    - Root static and XML sample locations
    - Original statistics paths

18. Remove old empty directories only after the reference search is clean.

19. Update every component README with exact setup, test and deployment commands.

20. Merge the migration as a sequence of focused commits:

    1. Documentation and CMS manifest
    2. Storefront assets and workflow
    3. Inventory service and workflow
    4. Product-import relocation
    5. Catalogue-audit tool
    6. Reporting and image tools
    7. Reference data
    8. CMS quarantine
    9. Final cleanup

## Verification

1. **Product import**
   - Run the complete pytest suite.
   - Build and start Docker Compose.
   - Verify `/health`, UI loading, persistent data and dry-run XML/image generation.

2. **Inventory sync**
   - Run `dotnet build` and new tests.
   - Generate XML from controlled LST fixtures.
   - Compare the result semantically with the baseline.
   - Verify exclusions and delivery calculations.
   - Manually dispatch the workflow before relying on the next schedule.

3. **Storefront assets**
   - Run minification from the new location.
   - Compare generated names with the baseline.
   - Dispatch the workflow and verify the remote destination remains `assets/`.

4. **Catalogue audit**
   - Run fixture-based comparison tests.
   - Perform one browser smoke run.
   - Confirm generated output remains ignored.

5. **Repository integrity**
   - Confirm no secrets, supplier snapshots, build outputs or generated reports became tracked.
   - Ensure test runs leave a clean Git status.
   - Verify all references to old paths have been removed.

6. **CMS snippets**
   - Verify each promoted file manually in DanDomain.
   - Delete obsolete files in a separate reviewed commit.

## Decisions

- Remain a monorepo.
- Treat scheduled inventory synchronization as a production service.
- Use incremental, reversible commits.
- Keep and rehabilitate the scraper as a catalogue-audit tool.
- Retain all remaining CMS source files as required; required status does not replace live-location verification.
- Keep unverified required CMS content in review until its live location is confirmed.
- Use Git history rather than permanent backup directories.
- Preserve current production behavior and remote deployment destinations.
- Exclude broad application rewrites, DanDomain contract changes and shared-library extraction from this restructuring.
