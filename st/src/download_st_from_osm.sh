#!/bin/bash

set -euo pipefail

echo "Download Serbia PBF from geofabrik"
mkdir -p data/osm/download
yesterday=`date -d "yesterday" +"%y%m%d"`
echo "Downloading serbia-$yesterday.osm.pbf"


attempts=0

if [ ! -f data/osm/download/serbia.osm.pbf ]; then
  max_attempts=36  # 36 * 5 min = 3h
  success=false

  while [ $attempts -lt $max_attempts ] && [ "$success" = false ]; do
    if wget https://download.geofabrik.de/europe/serbia-$yesterday.osm.pbf -O data/osm/download/serbia.osm.pbf -q --show-progress --progress=dot:giga; then
      success=true
    else
      attempts=$((attempts + 1))
      echo "Download failed. Attempt $attempts of $max_attempts. Retrying in 5 minutes..."
      rm -f data/osm/download/serbia.osm.pbf
      sleep 300
    fi
  done

  if [ "$success" = false ]; then
    echo "Failed to download after 3 hours of attempts (reached maximum of $max_attempts attempts)"
    exit 1
  fi
fi

if [ $attempts -gt 0 ]; then
  echo "Download succeeded after $attempts retries. Sleeping for additional 10 minutes to give time for AR module to complete..."
  sleep 600
fi

osm_data_date=`osmium fileinfo data/osm/download/serbia.osm.pbf | grep osmosis_replication_timestamp | cut -d"=" -f2`
osm_data_date=${osm_data_date::-1}
echo $osm_data_date
echo $osm_data_date > data/running
echo "Extracting addresses from PBF"
python3 src/download_st_from_osm.py
