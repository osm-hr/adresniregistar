#!/bin/bash

set -euo pipefail

test -f serbia.osm.pbf || wget http://download.geofabrik.de/europe/serbia-latest.osm.pbf -O serbia.osm.pbf -q --show-progress --progress=dot:giga

sudo service docker-overpass-rt stop
docker rm overpass_serbia_rt
rm -rf /mnt/ubicassd/overpass_db/

mkdir -p /mnt/ubicassd/overpass_db/

docker run \
  -e OVERPASS_META=yes \
  -e OVERPASS_MODE=init \
  -e OVERPASS_PLANET_URL=http://download.geofabrik.de/europe/serbia-latest.osm.pbf \
  -e OVERPASS_DIFF_URL=https://planet.openstreetmap.org/replication/minute/ \
  -e OVERPASS_RULES_LOAD=10 \
  -e OVERPASS_PLANET_PREPROCESS='mv /db/planet.osm.bz2 /db/planet.osm.pbf && osmium cat -o /db/planet.osm.bz2 /db/planet.osm.pbf && rm /db/planet.osm.pbf' \
  -v /mnt/ubicassd/overpass_db/:/db \
  -p 12346:80 \
  -i \
  --name overpass_serbia_rt wiktorn/overpass-api

sudo service docker-overpass-rt start
rm serbia.osm.pbf