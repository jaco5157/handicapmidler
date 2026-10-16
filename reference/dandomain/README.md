# DanDomain XML references

Single-product examples retained unchanged from the pre-migration sources, not import payloads for live use.

| File | Purpose | Source date and provenance |
| --- | --- | --- |
| [product-export-example.xml](product-export-example.xml) | Product-import structure, descriptions, categories, prices and media | First tracked 2026-06-21 in `be01118` as root `export.xml` |
| [product-export-all-fields-example.xml](product-export-all-fields-example.xml) | Broader field coverage, including stock, internal IDs and product administration metadata | First tracked 2026-09-29 in `2582c5e` as root `export-sample-all-fields.xml` |

The actual export dates are unknown. The dates above are Git source dates; product creation/edit timestamps inside the XML are not export timestamps. Both original versions are recoverable from `pre-restructure-2026-10-01`.

**Production-data status:** Both files are unsanitized, production-derived catalogue data. Real product numbers, descriptions, prices, image paths and internal metadata are intentionally retained for contract reference. Do not treat them as sanitized test fixtures or upload them to production. New production exports belong in ignored local storage, not this directory.