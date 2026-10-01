# Plan: Restructure Webshop Monorepo

Keep one repository, but reorganize it around clear deployment and ownership boundaries. Execute the migration as incremental, reversible commits while preserving current production behavior.

## Target organization

- **services**
  - **product-import** — FastAPI product import application
  - **inventory-sync** — scheduled .NET inventory integration
- **storefront**
  - **assets** — automatically deployed CSS and JavaScript
  - **cms-snippets/active** — verified, manually installed DanDomain snippets
  - **cms-snippets/review** — quarantined content with uncertain usage
  - **brand** — current logos and brand sources
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
   - Purpose and owner
   - Runtime or invocation method
   - Inputs and outputs
   - Deployment trigger and destination
   - Required secrets
   - Test and rollback procedure
5. Inventory every file under static. Record status, live CMS location, replacement, owner, last verification date and review deadline.

## Phase 2 — Establish production boundaries

6. Move deploy into the storefront asset area.
   - Update all path filters, minification paths, verification paths and FTP source paths in deploy-workflow.yml.
   - Preserve the remote `assets/` destination and generated filenames.
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

14. Move all unverified content from static into the CMS review quarantine.
    - Group it into pages, components and styles.
    - Promote files only after confirming their live DanDomain location.
    - Delete confirmed `backup`, `copy` and superseded files after the review deadline.
    - Use the pre-migration tag and Git history instead of creating a permanent archive folder.

15. Review graphics and move the SVG into the brand area only if it is a current source asset.

## Phase 5 — Integration and cleanup

16. Update .gitignore for:
    - Build output
    - Service-local data
    - Generated reports and catalogue results
    - Python environments
    - Secrets
    - OS metadata
    - Tool working directories

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
   - Record its live location and verification date in the manifest.
   - Delete obsolete files in a separate reviewed commit.

## Decisions

- Remain a monorepo.
- Treat scheduled inventory synchronization as a production service.
- Use incremental, reversible commits.
- Keep and rehabilitate the scraper as a catalogue-audit tool.
- Quarantine uncertain CMS content before deleting it.
- Use Git history rather than permanent backup directories.
- Preserve current production behavior and remote deployment destinations.
- Exclude broad application rewrites, DanDomain contract changes and shared-library extraction from this restructuring.
