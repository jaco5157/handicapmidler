# Handicapmidler webshop monorepo

Applications, integrations, storefront assets, CMS snippets, and operational tools for Handicapmidler.dk. Deployment and ownership boundaries are documented in [Architecture](docs/ARCHITECTURE.md).

## Production services

| Component | Current location | Purpose | Operation |
| --- | --- | --- | --- |
| Product import | [services/product-import](services/product-import/README.md) | Review supplier products and generate/upload DanDomain product XML and images | FastAPI in Docker Compose on DietPi; operator-driven UI |
| Inventory synchronization | [services/inventory-sync](services/inventory-sync/README.md) | Generate and import stock XML from supplier exports | .NET 8 console app; scheduled and manually dispatched GitHub Actions workflow |

## Storefront

| Component | Current location | Purpose | Operation |
| --- | --- | --- | --- |
| Automatically deployed assets | `storefront/assets` | Storefront JavaScript, CSS and confirmed store logo | JavaScript/CSS minified on pushes to `main` affecting `storefront/assets/**`; assets synchronized to remote `assets/` |
| CMS snippets | `storefront/cms-snippets/active` | Manually installed DanDomain HTML, CSS, and JavaScript | All 12 required files have verified live usage; see the [CMS manifest](docs/CMS-MANIFEST.md) |
| Store logo source | `graphics/handicapmidler.svg` | Confirmed current store logo | Original retained; unchanged deployment copy at `storefront/assets/handicapmidler.svg` |

## Operational tools

| Tool | Current location | Purpose | Current status |
| --- | --- | --- | --- |
| Catalogue audit | [tools/catalog-audit](tools/catalog-audit/README.md) | Compare Mobilex catalogue products with a DanDomain export | Configurable CLI, pinned dependencies and comparison tests |
| Referral reporting | [tools/reporting/referrals](tools/reporting/referrals/README.md) | Summarize order referrer domains | Configurable CSV input and chart output; synthetic fixture only |
| Manual image preparation | [tools/image-prep](tools/image-prep/README.md) | Produce the four storefront JPEG variants | Explicit directories and isolated cleanup; product import's Pillow flow is authoritative for automation |

## Reference data

- [DanDomain XML examples](reference/dandomain/README.md): production-derived catalogue references with source dates and an explicit unsanitized-data classification.
- [Inventory fixtures](reference/inventory/README.md): small synthetic inputs exercised by the inventory tests.

Do not commit secrets, new production exports, supplier snapshots, generated reports, or service-local data. Root `inventory/` is ignored local storage, not reference data.

## Documentation

- [Architecture and component boundaries](docs/ARCHITECTURE.md)
- [Build, deployment, verification, and rollback runbook](docs/DEPLOYMENT.md)
- [DanDomain CMS snippet manifest](docs/CMS-MANIFEST.md)
- [Product-import deployment to DietPi](services/product-import/DEPLOY_DIETPI.md)

Keep any future unverified required CMS content in `storefront/cms-snippets/review` until its live location is confirmed.