#!/bin/bash

set -euo pipefail

COUNTRY=${COUNTRY:-serbia}

function start_local_instance() {
  is_running=`docker inspect -f {{.State.Health.Status}} overpass_croatia_rt`
  if [ "$is_running" = "healthy" ]; then
    return
  fi

  docker stop overpass_croatia_rt
  docker rm overpass_croatia_rt
  rm -rf data/overpass_db/

  mkdir -p data/overpass_db/

  docker run \
    -e OVERPASS_META=yes \
    -e OVERPASS_MODE=init \
    -e OVERPASS_PLANET_URL=https://download.geofabrik.de/europe/croatia-latest.osm.pbf \
    -e OVERPASS_DIFF_URL=https://planet.openstreetmap.org/replication/minute/ \
    -e OVERPASS_RULES_LOAD=10 \
    -e OVERPASS_PLANET_PREPROCESS='mv /db/planet.osm.bz2 /db/planet.osm.pbf && osmium cat -o /db/planet.osm.bz2 /db/planet.osm.pbf && rm /db/planet.osm.pbf' \
    -v `$pwd`/data/overpass_db/:/db \
    -p 12346:80 \
    -i \
    --name overpass_croatia_rt wiktorn/overpass-api

  docker start overpass_croatia_rt

  echo "Waiting for container to boot up"
  until [ "`docker inspect -f {{.State.Health.Status}} overpass_croatia_rt`" == "healthy" ]; do
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
  echo "Download $COUNTRY PBF from geofabrik"
  mkdir -p data/osm/download
  yesterday=`date -d "yesterday" +"%y%m%d"`

  if [ ! -f data/osm/download/$COUNTRY.osm.pbf ]; then
    attempts=0
    max_attempts=288  # 288 * 5 min = 24h
    success=false

    INTERNAL_URL="https://osm-internal.download.geofabrik.de/europe/$COUNTRY-${yesterday}-internal.osm.pbf"
    PUBLIC_URL="https://download.geofabrik.de/europe/$COUNTRY-$yesterday.osm.pbf"
    PBF_PATH="data/osm/download/$COUNTRY.osm.pbf"
    FALLBACK_TO_PUBLIC_PBF=${FALLBACK_TO_PUBLIC_PBF:-false}
    GEOFABRIK_OAUTH_COOKIE=""

    if [ -n "${OSM_USERNAME:-}" ]; then
      echo "Pokušavam dobiti Geofabrik Cookie za korisnika $OSM_USERNAME"
      GEOFABRIK_OAUTH_COOKIE=$(python3 src/get_geofabrik_cookie.py "$OSM_USERNAME" "${OSM_PASSWORD:-}") || GEOFABRIK_OAUTH_COOKIE=""
      if [ -n "$GEOFABRIK_OAUTH_COOKIE" ]; then
        echo "DEBUG: Cookie dobijen: ${GEOFABRIK_OAUTH_COOKIE:0:50}..."
      else
        echo "DEBUG: Cookie nije dobiven"
      fi
    fi

    if [ -z "$GEOFABRIK_OAUTH_COOKIE" ] && [ "$FALLBACK_TO_PUBLIC_PBF" != "true" ]; then
      echo "Internal PBF nije dostupan, a FALLBACK_TO_PUBLIC_PBF nije postavljen na true. Prekidam."
      exit 1
    fi

    while [ $attempts -lt $max_attempts ] && [ "$success" = false ]; do
      if [ -n "$GEOFABRIK_OAUTH_COOKIE" ] && echo "Downloading $INTERNAL_URL" && \
          wget "--header=Cookie: gf_download_oauth=${GEOFABRIK_OAUTH_COOKIE}" "$INTERNAL_URL" -O "$PBF_PATH" -q --show-progress --progress=dot:giga; then
        pbf_source=internal
        success=true
      elif [ "$FALLBACK_TO_PUBLIC_PBF" = "true" ] && echo "Downloading $PUBLIC_URL" && \
          wget "$PUBLIC_URL" -O "$PBF_PATH" -q --show-progress --progress=dot:giga; then
        pbf_source=public
        success=true
      else
        attempts=$((attempts + 1))
        echo "Download failed. Attempt $attempts of $max_attempts. Retrying in 5 minutes..."
        rm -f "$PBF_PATH"
        sleep 300
      fi
    done

    if [ "$success" = false ]; then
      echo "Failed to download after 3 hours of attempts (reached maximum of $max_attempts attempts)"
      exit 1
    fi

    mkdir -p data/osm/download/source
    echo "$pbf_source" > data/osm/download/source/PBF_SOURCE
  fi

  osm_data_date=`osmium fileinfo data/osm/download/$COUNTRY.osm.pbf | grep osmosis_replication_timestamp | cut -d"=" -f2`
  osm_data_date=${osm_data_date::-1}
  echo $osm_data_date
  echo $osm_data_date > data/running
	echo "Extracting addresses from PBF"
	python3 src/download_from_osm.py
	echo "Preparing OSM data for analysis"
fi
