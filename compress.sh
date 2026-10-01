# Step 1: Make folders for each type of image
mkdir -p ./Compress/p ./Compress/o ./Compress/r ./Compress/t

# Step 2: Copy images and add suffixes
# for file in ./Compress/*; do
find ./Compress/ -maxdepth 1 -type f | while read file; do
    filename=$(basename -- "$file")
    extension="${filename##*.}"
    filename="${filename%.*}"

    echo "Processing file: $file"

    # Apply trimming, border, and conversion to JPG in one command
    if ! magick "$file" -background white -alpha remove -alpha off -trim -bordercolor white \
            -quality 100 "./Compress/${filename}.jpg"; then
        echo "Error processing $file for trimming and conversion"
        continue
    fi

    # After trimming and converting, create copies with different suffixes
    cp "./Compress/${filename}.jpg" "./Compress/p/${filename}-p.jpg"
    cp "./Compress/${filename}.jpg" "./Compress/o/${filename}.jpg"
    cp "./Compress/${filename}.jpg" "./Compress/r/${filename}-r.jpg"
    cp "./Compress/${filename}.jpg" "./Compress/t/${filename}-t.jpg"
done

# Step 3: Run compression commands
caesiumclt -q 0 -o ./Compressed ./Compress/p/
caesiumclt --long-edge "525" -q 0 -o ./Compressed/ ./Compress/o/
caesiumclt --long-edge "320" -q 0 -o ./Compressed/ ./Compress/r/
caesiumclt --long-edge "320" -q 0 -o ./Compressed/ ./Compress/t/

# Step 4: Delete all contents from the ./Compress/ folder
rm -r ./Compress/*