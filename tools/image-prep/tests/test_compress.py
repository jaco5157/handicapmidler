import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "compress.sh"


class ImagePreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        for name in ("input", "work", "output", "bin"):
            (self.directory / name).mkdir()
        (self.directory / "input/source image.png").write_text("original")
        magick = self.directory / "bin/magick"
        magick.write_text('#!/usr/bin/env bash\ncp "$1" "${@: -1}"\n')
        caesium = self.directory / "bin/caesiumclt"
        caesium.write_text(
            '#!/usr/bin/env bash\nwhile [[ "$1" != "-o" ]]; do shift; done\n'
            'cp "${@: -1}"/*.jpg "$2/"\n'
        )
        magick.chmod(0o755)
        caesium.chmod(0o755)
        self.environment = dict(os.environ, PATH=str(self.directory / "bin") + os.pathsep + os.environ["PATH"])

    def run_tool(self, *extra):
        return subprocess.run(
            ["bash", str(SCRIPT), str(self.directory / "input"), str(self.directory / "work"),
             str(self.directory / "output"), *extra],
            cwd=self.directory, env=self.environment, capture_output=True, text=True,
        )

    def test_variants_and_cleanup_preserve_originals_and_unrelated_work(self):
        sentinel = self.directory / "work/keep.txt"
        sentinel.write_text("unrelated")
        result = self.run_tool()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.directory / "input/source image.png").read_text(), "original")
        self.assertEqual([path.name for path in (self.directory / "work").iterdir()], ["keep.txt"])
        self.assertEqual(
            sorted(path.name for path in (self.directory / "output").iterdir()),
            ["source image-p.jpg", "source image-r.jpg", "source image-t.jpg", "source image.jpg"],
        )

    def test_keep_work_preserves_temporary_workspace(self):
        result = self.run_tool("--keep-work")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(list((self.directory / "work").glob("image-prep.*"))), 1)

    def test_failure_cleans_only_its_own_workspace(self):
        (self.directory / "bin/magick").write_text("#!/usr/bin/env bash\nexit 1\n")
        result = self.run_tool()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.directory / "input/source image.png").exists())
        self.assertEqual(list((self.directory / "work").iterdir()), [])


if __name__ == "__main__":
    unittest.main()