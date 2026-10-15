# Manual Image Preparation

Manual-only utility requiring Bash, ImageMagick (`magick`) and Caesium CLI (`caesiumclt`) on `PATH`. The product-import service's Pillow implementation is authoritative for automated imports. Retain this utility until continuing manual use is confirmed; remove it separately if unused.

From the repository root:

```sh
bash tools/image-prep/compress.sh /absolute/path/to/images /absolute/path/to/work /absolute/path/to/output
bash -n tools/image-prep/compress.sh
python3 -m unittest discover -s tools/image-prep/tests -v
```

Input, work and output directories are explicit. Work and output must be outside the input directory. The tool processes top-level input files, trims/converts them, and creates `name-p.jpg` (original trimmed size), `name.jpg` (long edge 525), `name-r.jpg` and `name-t.jpg` (long edge 320).

**Cleanup is destructive within the per-run temporary workspace**, on success or failure. Original input files and unrelated working files are preserved. Add `--keep-work` to retain that workspace for inspection. Back up originals and use a dedicated output directory: existing output filenames may be overwritten, and failed runs can leave partial output.

Repository-local `input/`, `work/` and `output/` directories under this tool are ignored. Test doubles verify naming and cleanup safety without requiring the external binaries. Result files are uploaded manually; there is no automated deployment. Discard the dedicated output directory to roll back a run.