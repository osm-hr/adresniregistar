#!/bin/bash

set -e

DOWNLOAD_DIR="data/rgz/download"
UNZIP_DIR="data/rgz/unzip"
mkdir -p "$DOWNLOAD_DIR" "$UNZIP_DIR"

download_croatia() {
    local addr_url="https://geoportal.dgu.hr/services/atom/INSPIRE_Addresses_(AD).zip"
    local admin_url="https://geoportal.dgu.hr/services/atom/INSPIRE_Administrative_Units_(AU).zip"
    local addr_zip="$DOWNLOAD_DIR/INSPIRE_Addresses_(AD).zip"
    local admin_zip="$DOWNLOAD_DIR/INSPIRE_Administrative_Units_(AU).zip"

    if [ ! -f "$admin_zip" ]; then
        curl -L --fail --retry 5 --retry-delay 10 --retry-connrefused -o "$admin_zip" "$admin_url"
        unzip -q "$admin_zip" -d "$UNZIP_DIR"
        mv "$UNZIP_DIR/AdministrativeUnit.gml" "$UNZIP_DIR/AdministrativeUnitOpstina.gml"
        ln -sf "AdministrativeUnitOpstina.gml" "$UNZIP_DIR/AdministrativeUnitNaselje.gml"
    else
        echo "Zip datoteka sa administrativnim jedinicama postoji, preskačem preuzimanje."
    fi

    if [ ! -f "$addr_zip" ]; then
        curl -L --fail --retry 5 --retry-delay 10 --retry-connrefused -o "$addr_zip" "$addr_url"
        unzip -q "$addr_zip" -d "$UNZIP_DIR"
    else
        echo "Zip datoteka sa adresama postoji, preskačem preuzimanje."
    fi
}

download_slovenia() {
    local uuid="eaa37d47-ecc3-4d90-9916-717a6b2a977d"
    local url="https://eprostor.gov.si/imps/srv/eng/mef.export?version=2&uuid=$uuid"
    local outer_zip="$DOWNLOAD_DIR/slovenia_inspire.zip"
    local tmp_dir="$DOWNLOAD_DIR/slovenia_tmp"

    if [ ! -f "$outer_zip" ]; then
        curl -L --fail --retry 5 --retry-delay 10 --retry-connrefused -o "$outer_zip" "$url"
    else
        echo "Zip datoteka za Sloveniju postoji, preskačem preuzimanje."
    fi

    mkdir -p "$tmp_dir"
    unzip -q -o "$outer_zip" -d "$tmp_dir"

    local inner_dir="$tmp_dir/$uuid/public"

    local -A file_map=(
        ["SI.GURS.RPE.ad.Address.zip"]="Address.gml"
        ["SI.GURS.RPE.ad.AddressAreaName.zip"]="AdminUnitName.gml"
        ["SI.GURS.RPE.ad.PostalDescriptor.zip"]="PostalDescriptor.gml"
        ["SI.GURS.RPE.ad.ThoroughfareName.zip"]="ThoroughfareName.gml"
    )

    for zip_name in "${!file_map[@]}"; do
        local gml_name="${file_map[$zip_name]}"
        local zip_path="$inner_dir/$zip_name"
        if [ ! -f "$zip_path" ]; then
            echo "Upozorenje: $zip_path ne postoji" >&2
            continue
        fi
        local inner_tmp
        inner_tmp=$(mktemp -d)
        unzip -q "$zip_path" -d "$inner_tmp"
        local gml_file
        gml_file=$(find "$inner_tmp" -maxdepth 2 \( -name "*.gml" -o -name "*.xml" \) | head -1)
        if [ -n "$gml_file" ]; then
            cp "$gml_file" "$UNZIP_DIR/$gml_name"
        else
            echo "Upozorenje: nije pronađena GML/XML datoteka u $zip_name" >&2
        fi
        rm -rf "$inner_tmp"
    done

    local -A admin_map=(
        ["opcine"]="AdministrativeUnitOpstina.gml"
        ["naselja"]="AdministrativeUnitNaselje.gml"
    )
    local -A admin_urls=(
        ["opcine"]="https://eprostor.gov.si/ods/atom?id=9&type=data"
        ["naselja"]="https://eprostor.gov.si/ods/atom?id=8&type=data"
    )

    for key in "${!admin_map[@]}"; do
        local gml_name="${admin_map[$key]}"
        local admin_zip="$DOWNLOAD_DIR/slovenia_admin_${key}.zip"
        if [ ! -f "$admin_zip" ]; then
            curl -L --fail --retry 5 --retry-delay 10 --retry-connrefused -o "$admin_zip" "${admin_urls[$key]}"
        else
            echo "Zip datoteka za $gml_name postoji, preskačem preuzimanje."
        fi
        unzip -p "$admin_zip" > "$UNZIP_DIR/$gml_name"
    done
}

case "${COUNTRY:-croatia}" in
    croatia)
        download_croatia
        ;;
    slovenia)
        download_slovenia
        ;;
    *)
        echo "Greška: nepoznata zemlja '$COUNTRY'" >&2
        exit 1
        ;;
esac

INSPIRE_DATE=$(head -c 2000 "$UNZIP_DIR/Address.gml" \
  | grep -o 'timeStamp="[^"]*"' \
  | cut -d'"' -f2 \
  | cut -d'T' -f1)

echo "$INSPIRE_DATE" > data/rgz/LATEST

if [ "${COUNTRY:-croatia}" = "slovenia" ]; then
    sed -i -E 's|xlink:href="https://[^"]*&lt;Literal&gt;([^&]+)&lt;/Literal&gt;[^"]*"|xlink:href="#SI.GURS.RPE.\1"|g' \
        "$UNZIP_DIR/Address.gml"
    sed -i 's|<ad:AddressAreaName |<ad:AdminUnitName |g; s|</ad:AddressAreaName>|</ad:AdminUnitName>|g' \
        "$UNZIP_DIR/AdminUnitName.gml"
fi

./dgu-parse/target/release/dgu-parse ./data/rgz/unzip/ $ADDRESS_CRS
