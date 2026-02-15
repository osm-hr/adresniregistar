#!/bin/bash

set -e

DOWNLOAD_DIR="data/rgz/download"
UNZIP_DIR="data/rgz/unzip"
ADDR_URL="https://opendata.osm-hr.org/dgu/inspire-addresses/2025-11-10/INSPIRE_Addresses_(AD).zip"
ADMIN_URL="https://opendata.osm-hr.org/dgu/inspire-administrative-units/2024-12-10/podjela/AdministrativeUnit-jedinice-lokalne-samouprave-4326.geojson.gz"
ADDR_ZIP_FILE="$DOWNLOAD_DIR/INSPIRE_Addresses_(AD).zip"
ADMIN_ZIP_FILE="$DOWNLOAD_DIR/AdministrativeUnit-jedinice-lokalne-samouprave-4326.geojson.gz"
ADMIN_GEOJSON_FILE="opstina.geojson"
mkdir -p "$DOWNLOAD_DIR" "$UNZIP_DIR"

if [ ! -f "$ADDR_ZIP_FILE" ]; then
    curl -L -o "$ADDR_ZIP_FILE" "$ADDR_URL"

    unzip -q "$ADDR_ZIP_FILE" -d "$UNZIP_DIR"
else
    echo "Zip datoteka sa adresama postoji, preskačem preuzimanje."
fi

./dgu-parse/target/release/dgu-parse ./data/rgz/unzip/

duckdb -csv -c "$(cat src/dgu-query.sql)" > data/rgz/addresses.csv

if [ ! -f "$ADMIN_ZIP_FILE" ]; then
    curl -L -o "$ADMIN_ZIP_FILE" "$ADMIN_URL"

    gunzip -c "$ADMIN_ZIP_FILE" > "./data/rgz/$ADMIN_GEOJSON_FILE"
else
    echo "Zip datoteka sa administrativnim jedinicama postoji, preskačem preuzimanje."
fi