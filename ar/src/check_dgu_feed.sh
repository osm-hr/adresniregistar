#!/bin/bash
set -e

LATEST_FILE="data/rgz/LATEST"
ADDR_FEED="https://geoportal.dgu.hr/services/atom/ad/xml"

atom_entry_date() {
    curl -s "$1" | grep -A5 '<entry>' | grep '<updated>' | head -1 \
        | sed 's/.*<updated>\(.*\)<\/updated>.*/\1/' \
        | cut -dT -f1
}

LATEST_DATE=""
[ -f "$LATEST_FILE" ] && LATEST_DATE=$(cat "$LATEST_FILE")

ADDR_DATE=$(atom_entry_date "$ADDR_FEED")

echo "Adrese na feedu:  $ADDR_DATE"
echo "Lokalni LATEST:   ${LATEST_DATE:-<nema>}"

NEWER=$(printf '%s\n' "$LATEST_DATE" "$ADDR_DATE" | sort -r | head -1)

if [ -n "$LATEST_DATE" ] && [ "$NEWER" = "$LATEST_DATE" ]; then
    echo "Nema novih podataka."
    exit 0
fi

echo "Novi podaci dostupni ($ADDR_DATE)."
exit 1