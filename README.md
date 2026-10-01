# Handicapmidler webshop monorepo

Applications, integrations, storefront assets, CMS snippets, and operational tools for Handicapmidler.dk. The repository is being reorganized around deployment and ownership boundaries; current and target paths are documented in [Architecture](docs/ARCHITECTURE.md).

## Production services

| Component | Current location | Purpose | Operation |
| --- | --- | --- | --- |
| Product import | [services/product-import-service](services/product-import-service/README.md) | Review supplier products and generate/upload DanDomain product XML and images | FastAPI in Docker Compose on DietPi; operator-driven UI |
| Inventory synchronization | `scripts/InventoryService` | Generate and import stock XML from supplier exports | .NET 8 console app; scheduled and manually dispatched GitHub Actions workflow |

## Storefront

| Component | Current location | Purpose | Operation |
| --- | --- | --- | --- |
| Automatically deployed assets | `deploy` | Storefront JavaScript and CSS | Minified on pushes to `main` affecting `deploy/**`, then synchronized to remote `assets/` |
| CMS snippets | `static` | Manually installed DanDomain HTML, CSS, and JavaScript | Unverified content; see [CMS manifest](docs/CMS-MANIFEST.md) before use |
| Brand candidate | `graphics` | SVG logo/brand source | Current use is not yet verified |

## Operational tools

| Tool | Current location | Purpose | Current status |
| --- | --- | --- | --- |
| Catalogue audit | `scripts/product-scraper` | Compare Mobilex catalogue products with a DanDomain export | Retained for repair; current generated paths are broken |
| Referral reporting | `scripts/statistics` | Summarize order referrer domains | Manual Python utility with a fixed input path |
| Manual image preparation | `compress.sh` | Produce the four storefront JPEG variants | Manual/destructive working-directory tool; product import's Pillow flow is authoritative for automation |

## Reference data

- `export.xml` and `export-sample-all-fields.xml` are DanDomain XML examples pending review and relocation.
- `inventory/` contains supplier-format samples/snapshots pending sanitization review.

Do not commit secrets, production exports, supplier snapshots, generated reports, or service-local data.

## Documentation

- [Architecture and component boundaries](docs/ARCHITECTURE.md)
- [Build, deployment, verification, and rollback runbook](docs/DEPLOYMENT.md)
- [Phase 1 baseline](docs/PHASE-1-BASELINE.md)
- [DanDomain CMS snippet manifest](docs/CMS-MANIFEST.md)
- [Product-import deployment to DietPi](services/product-import-service/DEPLOY_DIETPI.md)

Operational owners and CMS locations are deliberately marked unassigned/unverified where repository evidence is insufficient. Assign and verify them before promoting or deleting content.