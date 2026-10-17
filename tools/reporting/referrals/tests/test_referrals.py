import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

os.environ["MPLBACKEND"] = "Agg"
TOOL_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("referrals", TOOL_DIR / "referrals.py")
referrals = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(referrals)


class ReferralTests(unittest.TestCase):
    def test_domain_normalization(self):
        self.assertEqual(referrals.clean_referrer("https://WWW.Example.com/path"), "example.com")
        self.assertEqual(referrals.clean_referrer("example.com/path"), "example.com")
        self.assertEqual(referrals.clean_referrer(None), "Unknown")
        self.assertEqual(referrals.clean_referrer(""), "Unknown")

    def test_synthetic_fixture_counts(self):
        counts = referrals.count_referrers(TOOL_DIR / "fixtures/referrals.csv")
        self.assertEqual(counts.to_dict(), {"example.com": 2, "search.example.org": 1, "Unknown": 1})

    def test_cli_saves_chart_from_unrelated_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output/chart.png"
            subprocess.run(
                [sys.executable, str(TOOL_DIR / "referrals.py"), "--input",
                 str(TOOL_DIR / "fixtures/referrals.csv"), "--output", str(output)],
                cwd=directory, check=True, capture_output=True,
            )
            self.assertGreater(output.stat().st_size, 0)

    def test_missing_column_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "wrong.csv"
            source.write_text("OTHER\nvalue\n")
            with self.assertRaises(ValueError):
                referrals.count_referrers(source)


if __name__ == "__main__":
    unittest.main()