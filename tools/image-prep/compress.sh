#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 || $# -gt 4 || ( $# -eq 4 && "$4" != "--keep-work" ) ]]; then
    echo "Usage: $0 INPUT_DIR WORK_DIR OUTPUT_DIR [--keep-work]" >&2
    exit 2
fi
command -v magick >/dev/null
command -v caesiumclt >/dev/null
input_dir=$(cd "$1" && pwd -P)
mkdir -p "$2" "$3"
work_root=$(cd "$2" && pwd -P)
output_dir=$(cd "$3" && pwd -P)
for target in "$work_root" "$output_dir"; do
    case "$target/" in
        "$input_dir/"*) echo "Work and output directories must be outside input" >&2; exit 2 ;;
    esac
done
work_dir=$(mktemp -d "$work_root/image-prep.XXXXXX")
if [[ $# -eq 4 ]]; then
    echo "Keeping temporary files: $work_dir" >&2
else
    echo "Temporary working files will be deleted; original inputs are preserved" >&2
    trap 'rm -rf -- "$work_dir"' EXIT
fi
mkdir -p "$work_dir/p" "$work_dir/o" "$work_dir/r" "$work_dir/t"
processed=0
while IFS= read -r -d '' file; do
    filename=$(basename -- "$file")
    filename="${filename%.*}"
    magick "$file" -background white -alpha remove -alpha off -trim -bordercolor white \
        -quality 100 "$work_dir/$filename.jpg"
    cp "$work_dir/$filename.jpg" "$work_dir/p/$filename-p.jpg"
    cp "$work_dir/$filename.jpg" "$work_dir/o/$filename.jpg"
    cp "$work_dir/$filename.jpg" "$work_dir/r/$filename-r.jpg"
    cp "$work_dir/$filename.jpg" "$work_dir/t/$filename-t.jpg"
    processed=$((processed + 1))
done < <(find "$input_dir" -maxdepth 1 -type f -print0)
if [[ $processed -eq 0 ]]; then
    echo "No input files found" >&2
    exit 1
fi
caesiumclt -q 0 -o "$output_dir" "$work_dir/p/"
caesiumclt --long-edge 525 -q 0 -o "$output_dir" "$work_dir/o/"
caesiumclt --long-edge 320 -q 0 -o "$output_dir" "$work_dir/r/"
caesiumclt --long-edge 320 -q 0 -o "$output_dir" "$work_dir/t/"