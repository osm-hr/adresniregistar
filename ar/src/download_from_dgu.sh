#!/bin/bash

set -e

DOWNLOAD_DIR="data/rgz/download"
UNZIP_DIR="data/rgz/unzip"
DGU_DATE="2025-11-10"
ADDR_URL="https://opendata.osm-hr.org/dgu/inspire-addresses/${DGU_DATE}/INSPIRE_Addresses_(AD).zip"
ADMIN_URL="https://opendata.osm-hr.org/dgu/inspire-administrative-units/${DGU_DATE}/INSPIRE_Administrative_Units_(AU).zip"
ADDR_ZIP_FILE="$DOWNLOAD_DIR/INSPIRE_Addresses_(AD).zip"
ADMIN_ZIP_FILE="$DOWNLOAD_DIR/INSPIRE_Administrative_Units_(AU).zip"
ADMIN_GEOJSON_FILE="opstina.geojson"
mkdir -p "$DOWNLOAD_DIR" "$UNZIP_DIR"

if [ ! -f "$ADMIN_ZIP_FILE" ]; then
    curl -L -o "$ADMIN_ZIP_FILE" "$ADMIN_URL"

    unzip -q "$ADMIN_ZIP_FILE" -d "$UNZIP_DIR"
else
    echo "Zip datoteka sa administrativnim jedinicama postoji, preskačem preuzimanje."
fi

if [ ! -f "$ADDR_ZIP_FILE" ]; then
    curl -L -o "$ADDR_ZIP_FILE" "$ADDR_URL"

    unzip -q "$ADDR_ZIP_FILE" -d "$UNZIP_DIR"
else
    echo "Zip datoteka sa adresama postoji, preskačem preuzimanje."
fi

echo $DGU_DATE > data/rgz/LATEST

./dgu-parse/target/release/dgu-parse ./data/rgz/unzip/