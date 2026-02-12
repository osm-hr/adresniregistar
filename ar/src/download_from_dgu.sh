#!/bin/bash

set -e

DOWNLOAD_DIR="data/rgz/download"
UNZIP_DIR="data/rgz/unzip"
URL="https://opendata.osm-hr.org/dgu/inspire-addresses/2025-11-10/INSPIRE_Addresses_(AD).zip"
ZIP_FILE="$DOWNLOAD_DIR/INSPIRE_Addresses_(AD).zip"

mkdir -p "$DOWNLOAD_DIR" "$UNZIP_DIR"

if [ ! -f "$ZIP_FILE" ]; then
    curl -L -o "$ZIP_FILE" "$URL"

    unzip -q "$ZIP_FILE" -d "$UNZIP_DIR"
else
    echo "Zip datoteka postoji, preskačem preuzimanje."
fi

cd dgu-parse
cargo build --release
cd ..
./dgu-parse/target/release/dgu-parse ./data/rgz/unzip/

duckdb -csv -c "$(cat src/dgu-query.sql)" > data/rgz/addresses.csv