# DanDomain CMS snippet manifest

Revised on 2026-10-09. This manifest covers all 18 files currently tracked under `static/`. Every unclassified file remains in **Review** because its current use could not be confirmed from the repository alone. The original 34-file inventory remains available from Git history and tag `pre-restructure-2026-10-01`.

## Status rules

- **Active:** Confirmed to be in use. It will move to `storefront/cms-snippets/active`.
- **Review:** Not yet confirmed. It will move to `storefront/cms-snippets/review` so it can be checked later.
- **Delete:** Confirmed unused. It will be deleted in a separate reviewed commit, not during the initial move.

To classify a file, only change its **Status** cell to `Active`, `Review`, or `Delete`. Files still marked `Review` will never be deleted automatically.

These classifications are applied during **Phase 4 (CMS quarantine)**, not Phase 2. Phase 2 only moves the storefront assets and production services. Git history and tag `pre-restructure-2026-10-01` remain available for recovery.

## Document snippets

| Current file | Type / probable purpose | Status |
| --- | --- | --- |
| `static/documents/about.html` | About page content | Review |
| `static/documents/basket.html` | Basket page content | Review |
| `static/documents/footer.html` | Storefront footer content | Review |
| `static/documents/frontpage.html` | Front page content | Review |
| `static/documents/subcat.css` | Subcategory page styling | Review |
| `static/documents/subcat.html` | Subcategory page markup | Review |

## Subcategory snippets

| Current file | Type / probable purpose | Status |
| --- | --- | --- |
| `static/subcats/badestole.html` | Bath-chair category content | Review |
| `static/subcats/dæk-punkterfri.html` | Puncture-free tyre category content | Review |
| `static/subcats/dæk.html` | Tyre category content | Review |
| `static/subcats/forhjul.html` | Front-wheel category content | Review |
| `static/subcats/kørestole.html` | Wheelchair category content | Review |
| `static/subcats/puder.html` | Cushion category content | Review |
| `static/subcats/ramper.html` | Ramp category content | Review |
| `static/subcats/toilettet.html` | Toilet-aid category content | Review |

## Reusable templates

| Current file | Type / probable purpose | Status |
| --- | --- | --- |
| `static/templates/confirmationMail.html` | Order confirmation email template | Review |
| `static/templates/corfirmationLines.html` | Confirmation line-item template; filename contains a typo | Review |
| `static/templates/product-info-table.html` | Product specification table template | Review |
| `static/templates/video-wrapper.html` | Embedded product video wrapper | Review |

## Verification procedure

For each file:

1. Check whether the file is currently used in DanDomain.
2. Set its status to `Active`, `Review`, or `Delete`.
3. During Phase 4, move `Active` files to `active` and `Review` files to `review`.
4. Delete `Delete` files only in a separate reviewed commit.
