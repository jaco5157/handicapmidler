# Handicapmidler webshop monorepo

Applications, integrations, storefront assets, CMS snippets, and operational tools for Handicapmidler.dk. The repository is being reorganized around deployment and ownership boundaries; current and target paths are documented in [Architecture](docs/ARCHITECTURE.md).

## Production services

| Component | Current location | Purpose | Operation |
| --- | --- | --- | --- |
| Product import | [services/product-import](services/product-import/README.md) | Review supplier products and generate/upload DanDomain product XML and images | FastAPI in Docker Compose on DietPi; operator-driven UI |
| Inventory synchronization | [services/inventory-sync](services/inventory-sync/README.md) | Generate and import stock XML from supplier exports | .NET 8 console app; scheduled and manually dispatched GitHub Actions workflow |

## Storefront

| Component | Current location | Purpose | Operation |
| --- | --- | --- | --- |
| Automatically deployed assets | `storefront/assets` | Storefront JavaScript and CSS | Minified on pushes to `main` affecting `storefront/assets/**`, then synchronized to remote `assets/` |
| CMS snippets | `static` | Manually installed DanDomain HTML, CSS, and JavaScript | Required content; live locations await verification in the [CMS manifest](docs/CMS-MANIFEST.md) |
| Brand candidate | `graphics` | SVG logo/brand source | Current use is not yet verified |

## Operational tools

| Tool | Current location | Purpose | Current status |
| --- | --- | --- | --- |
| Catalogue audit | [tools/catalog-audit](tools/catalog-audit/README.md) | Compare Mobilex catalogue products with a DanDomain export | Configurable CLI, pinned dependencies and comparison tests |
| Referral reporting | [tools/reporting/referrals](tools/reporting/referrals/README.md) | Summarize order referrer domains | Configurable CSV input and chart output; synthetic fixture only |
| Manual image preparation | [tools/image-prep](tools/image-prep/README.md) | Produce the four storefront JPEG variants | Explicit directories and isolated cleanup; product import's Pillow flow is authoritative for automation |

## Reference data

- `export.xml` and `export-sample-all-fields.xml` are DanDomain XML examples pending review and relocation.
- `inventory/` contains supplier-format samples/snapshots pending sanitization review.

Do not commit secrets, production exports, supplier snapshots, generated reports, or service-local data.

## Documentation

- [Architecture and component boundaries](docs/ARCHITECTURE.md)
- [Build, deployment, verification, and rollback runbook](docs/DEPLOYMENT.md)
- [Phase 1 baseline](docs/PHASE-1-BASELINE.md)
- [DanDomain CMS snippet manifest](docs/CMS-MANIFEST.md)
- [Product-import deployment to DietPi](services/product-import/DEPLOY_DIETPI.md)

Verify live CMS locations before promoting content.