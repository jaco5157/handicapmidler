# DanDomain CMS snippet manifest

Captured on 2026-10-01. This manifest covers all 34 files tracked under `static/` before restructuring. Every file starts in **Review** because its current use could not be confirmed from the repository alone.

## Status rules

- **Active:** Confirmed to be in use. It will move to `storefront/cms-snippets/active`.
- **Review:** Not yet confirmed. It will move to `storefront/cms-snippets/review` so it can be checked later.
- **Delete:** Confirmed unused. It will be deleted in a separate reviewed commit, not during the initial move.

To classify a file, only change its **Status** cell to `Active`, `Review`, or `Delete`. Files still marked `Review` will never be deleted automatically.

These classifications are applied during **Phase 4 (CMS quarantine)**, not Phase 2. Phase 2 only moves the storefront assets and production services. Git history and tag `pre-restructure-2026-10-01` remain available for recovery.

## Root snippets

| Current file | Type / probable purpose | Status |
| --- | --- | --- |
| `static/backup-variantselector-new copy.js` | Variant selector script copy | Review |
| `static/backup-variantselector-new.css` | Variant selector style backup | Review |
| `static/backup-variantselector-new.js` | Variant selector script backup | Review |
| `static/backup-variantselector.css` | Variant selector style backup | Review |
| `static/backup-variantselector.js` | Variant selector script backup | Review |
| `static/backup.css` | Unidentified style backup | Review |
| `static/backup.html` | Unidentified HTML backup | Review |
| `static/backup.js` | Unidentified script backup | Review |
| `static/color-palette.css` | Shared colour definitions | Review |
| `static/confirmationMail.html` | Order confirmation email template | Review |
| `static/corfirmationLines.html` | Confirmation line-item template; filename contains a typo | Review |
| `static/get-cvr.js` | CVR lookup script | Review |
| `static/get.cvr.html` | CVR lookup markup | Review |
| `static/inventory.html` | Inventory/availability markup | Review |
| `static/metadata-fetcher.js` | Metadata helper script | Review |
| `static/more-info-button.html` | Product more-information button | Review |
| `static/orderStepRadio.css` | Checkout radio-button styling | Review |
| `static/star-rating.css` | Product rating styling | Review |
| `static/styles-backup.css` | General style backup | Review |

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
| `static/templates/product-info-table.html` | Product specification table template | Review |

## Verification procedure

For each file:

1. Check whether the file is currently used in DanDomain.
2. Set its status to `Active`, `Review`, or `Delete`.
3. During Phase 4, move `Active` files to `active` and `Review` files to `review`.
4. Delete `Delete` files only in a separate reviewed commit.
