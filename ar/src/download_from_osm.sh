#!/bin/bash

set -euo pipefail

function start_local_instance() {
  is_running=`docker inspect -f {{.State.Health.Status}} overpass_serbia_rt`
  if [ "$is_running" = "healthy" ]; then
    return
  fi

  docker stop overpass_serbia_rt
  docker rm overpass_serbia_rt
  rm -rf data/overpass_db/

  mkdir -p data/overpass_db/

  docker run \
    -e OVERPASS_META=yes \
    -e OVERPASS_MODE=init \
    -e OVERPASS_PLANET_URL=https://download.geofabrik.de/europe/serbia-latest.osm.pbf \
    -e OVERPASS_DIFF_URL=https://planet.openstreetmap.org/replication/minute/ \
    -e OVERPASS_RULES_LOAD=10 \
    -e OVERPASS_PLANET_PREPROCESS='mv /db/planet.osm.bz2 /db/planet.osm.pbf && osmium cat -o /db/planet.osm.bz2 /db/planet.osm.pbf && rm /db/planet.osm.pbf' \
    -v `$pwd`/data/overpass_db/:/db \
    -p 12346:80 \
    -i \
    --name overpass_serbia_rt wiktorn/overpass-api

  docker start overpass_serbia_rt

  echo "Waiting for container to boot up"
  until [ "`docker inspect -f {{.State.Health.Status}} overpass_serbia_rt`" == "healthy" ]; do
      date
      echo "Still waiting for container to boot up"
      sleep 5
  done;

  sleep 10
}


if [ "${AR_INCREMENTAL_UPDATE:-}" = "1" ]; then
  if test -f "data/running"; then
      echo "data/running.pid exists. Check if script is executing and delete before running again"
      exit 1
  fi
  osm_data_date=`date +%Y-%m-%dT%H:%M:%S`
  echo $osm_data_date
  echo $osm_data_date > data/running
	echo "Getting all addresses from overpass"
	python3 src/download_from_overpass.py
else
  echo "Download Serbia PBF from geofabrik"
  mkdir -p data/osm/download
  yesterday=`date -d "yesterday" +"%y%m%d"`
  echo "Downloading croatia-$yesterday.osm.pbf"

  if [ ! -f data/osm/download/croatia.osm.pbf ]; then
    attempts=0
    max_attempts=36  # 36 * 5 min = 3h
    success=false

    while [ $attempts -lt $max_attempts ] && [ "$success" = false ]; do
      if wget https://download.geofabrik.de/europe/croatia-$yesterday.osm.pbf -O data/osm/download/croatia.osm.pbf -q --show-progress --progress=dot:giga; then
        success=true
      else
        attempts=$((attempts + 1))
        echo "Download failed. Attempt $attempts of $max_attempts. Retrying in 5 minutes..."
        rm -f data/osm/download/croatia.osm.pbf
        sleep 300
      fi
    done

    if [ "$success" = false ]; then
      echo "Failed to download after 3 hours of attempts (reached maximum of $max_attempts attempts)"
      exit 1
    fi
  fi

  osm_data_date=`osmium fileinfo data/osm/download/croatia.osm.pbf | grep osmosis_replication_timestamp | cut -d"=" -f2`
  osm_data_date=${osm_data_date::-1}
  echo $osm_data_date
  echo $osm_data_date > data/running
	echo "Extracting addresses from PBF"
	python3 src/download_from_osm.py
	echo "Preparing OSM data for analysis"
fi
