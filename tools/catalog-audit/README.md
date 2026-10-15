# Catalogue Audit

Find Mobilex catalogue products missing from a DanDomain export. This audits catalogue gaps; single-product creation remains in the product-import service.

## Setup and run

Python 3.11+ and Chrome/Chromium are required. From the repository root:

```sh
cd tools/catalog-audit
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scraper.py
.venv/bin/python product-comparer.py --export-xml /absolute/path/to/webshop-export.xml
```

Defaults live in tool-local `generated/`, independent of the working directory. The scraper writes semicolon-delimited `mobilex_products.csv`; the comparer writes comma-delimited `products_missing_in_export.csv`. Generated files are ignored, including copied webshop exports.

Scraper options: `--output FILE`, repeatable `--start-url URL`, and `--workers COUNT` (default 4). Comparison options: `--supplier-csv FILE`, `--export-xml FILE`, and `--output FILE`. Explicit relative paths resolve from the invocation directory.

Use a matched browser/driver pair. Set `CHROME_BIN` and `SELENIUM_DRIVER_PATH` for system installations; otherwise webdriver-manager obtains a driver for Chrome. A browser mismatch is an environment error, not an empty catalogue.

Supplier CSV requires `product_number`, `product_name`, `category_name`, and `product_url`. Product identifiers remain strings; duplicates and the existing excluded categories are removed. XML must contain `PRODUCT_EXPORT/ELEMENTS/PRODUCT/GENERAL/PROD_NUM`.

## Verification

From this tool directory:

```sh
.venv/bin/python -m unittest discover -s tests -v
CATALOG_BROWSER_SMOKE=1 .venv/bin/python -m unittest discover -s tests -v
```

The first command is offline. The second also opens a live supplier catalogue page in headless Chrome. It needs network access and a matched driver. No webshop uploads occur. There is no deployment step; discard generated reports to roll back a run.