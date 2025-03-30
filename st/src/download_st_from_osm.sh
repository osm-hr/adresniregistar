#!/bin/bash

set -euo pipefail

echo "Download Serbia PBF from geofabrik"
mkdir -p data/osm/download
yesterday=`date -d "yesterday" +"%y%m%d"`
echo "Downloading serbia-$yesterday.osm.pbf"
test -f data/osm/download/serbia.osm.pbf || wget https://download.geofabrik.de/europe/serbia-$yesterday.osm.pbf -O data/osm/download/serbia.osm.pbf -q --show-progress --progress=dot:giga

osm_data_date=`osmium fileinfo data/osm/download/serbia.osm.pbf | grep osmosis_replication_timestamp | cut -d"=" -f2`
osm_data_date=${osm_data_date::-1}
echo $osm_data_date
echo $osm_data_date > data/running
echo "Extracting addresses from PBF"
python3 src/download_st_from_osm.py
