import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


TOOL_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("comparer", TOOL_DIR / "product-comparer.py")
comparer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(comparer)


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.csv = self.directory / "supplier.csv"
        self.xml = self.directory / "export.xml"
        self.csv.write_text(
            "product_number;product_name;category_name;product_url\n"
            "001;Existing;Chairs;https://example.invalid/1\n"
            "DF-240;Missing;Chairs;https://example.invalid/2\n"
            "DF-240;Duplicate;Chairs;https://example.invalid/2\n"
            "999;Excluded;Rollator;https://example.invalid/3\n"
        )
        self.xml.write_text(
            '<PRODUCT_EXPORT><ELEMENTS><PRODUCT><GENERAL><PROD_NUM>001</PROD_NUM>'
            '</GENERAL></PRODUCT></ELEMENTS></PRODUCT_EXPORT>'
        )

    def test_comparison_preserves_identifiers_filters_categories_and_deduplicates(self):
        supplier = comparer.get_mobilex_data(self.csv)
        self.assertEqual(supplier.product_number.tolist(), ["001", "DF-240"])
        result = comparer.list_products_missing_in_export(supplier, comparer.get_product_data(self.xml))
        self.assertEqual(result.product_number.tolist(), ["DF-240"])

    def test_empty_export_means_all_supplier_products_are_missing(self):
        self.xml.write_text("<PRODUCT_EXPORT><ELEMENTS/></PRODUCT_EXPORT>")
        result = comparer.list_products_missing_in_export(
            comparer.get_mobilex_data(self.csv), comparer.get_product_data(self.xml)
        )
        self.assertEqual(len(result), 2)

    def test_invalid_csv_and_xml_fail(self):
        self.csv.write_text("unexpected\nvalue\n")
        with self.assertRaises(ValueError):
            comparer.get_mobilex_data(self.csv)
        self.xml.write_text("<WRONG/>")
        with self.assertRaises(ValueError):
            comparer.get_product_data(self.xml)

    def test_cli_runs_from_unrelated_directory(self):
        output = self.directory / "nested/missing.csv"
        subprocess.run(
            [sys.executable, str(TOOL_DIR / "product-comparer.py"), "--supplier-csv", str(self.csv),
             "--export-xml", str(self.xml), "--output", str(output)],
            cwd=self.directory, check=True, capture_output=True,
        )
        self.assertEqual(pd.read_csv(output).product_number.tolist(), ["DF-240"])

    def test_default_paths_belong_to_tool(self):
        self.assertEqual(comparer.GENERATED_DIR, TOOL_DIR / "generated")


@unittest.skipUnless(os.environ.get("CATALOG_BROWSER_SMOKE") == "1", "Opt-in live browser smoke")
class BrowserSmokeTests(unittest.TestCase):
    def test_supplier_catalogue_page(self):
        specification = importlib.util.spec_from_file_location("scraper", TOOL_DIR / "scraper.py")
        scraper = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(scraper)
        driver = scraper.get_driver()
        try:
            products = scraper.scrape_mobilex_products(scraper.starting_urls[0], driver)
            self.assertFalse(products.empty)
            self.assertTrue(products.product_url.str.startswith("https://").all())
        finally:
            driver.quit()


if __name__ == "__main__":
    unittest.main()