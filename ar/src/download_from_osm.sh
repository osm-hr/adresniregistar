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
  yesterday=`date -d "2 days ago" +"%y%m%d"`
  echo "Downloading $COUNTRY-$yesterday.osm.pbf"

  if [ ! -f data/osm/download/$COUNTRY.osm.pbf ]; then
    attempts=0
    max_attempts=240  # 240 * 5 min = 20h
    success=false

    # If GEOFABRIK_OAUTH_COOKIE is set, download internal extract (with full metadata: changeset, uid, user)
    # Get cookie by logging in at https://osm-internal.download.geofabrik.de with your OSM account,
    # then copying the value of the "gf_download_oauth" cookie from browser DevTools.
    if [ -n "${OSM_USERNAME:-}" ]; then
      echo "Getting Geofabrik Cookie for user $OSM_USERNAME"
      GEOFABRIK_OAUTH_COOKIE= python3 src/get_geofabrik_cookie.py "$OSM_USERNAME" "$OSM_PASSWORD"
      DOWNLOAD_URL="https://osm-internal.download.geofabrik.de/europe/$COUNTRY-${yesterday}-internal.osm.pbf"
      WGET_ARGS=("--header=Cookie: gf_download_oauth=${GEOFABRIK_OAUTH_COOKIE}")
      echo "Using internal Geofabrik extract (full metadata)"
    else
      DOWNLOAD_URL="https://download.geofabrik.de/europe/$COUNTRY-$yesterday.osm.pbf"
      WGET_ARGS=()
      echo "Using public Geofabrik extract (no changeset/uid/user metadata)"
    fi

    while [ $attempts -lt $max_attempts ] && [ "$success" = false ]; do
      if wget "${WGET_ARGS[@]}" "$DOWNLOAD_URL" -O data/osm/download/$COUNTRY.osm.pbf -q --show-progress --progress=dot:giga; then
        success=true
      else
        attempts=$((attempts + 1))
        echo "Download failed. Attempt $attempts of $max_attempts. Retrying in 5 minutes..."
        rm -f data/osm/download/$COUNTRY.osm.pbf
        sleep 300
      fi
    done

    if [ "$success" = false ]; then
      echo "Failed to download after 3 hours of attempts (reached maximum of $max_attempts attempts)"
      exit 1
    fi
  fi

  osm_data_date=`osmium fileinfo data/osm/download/$COUNTRY.osm.pbf | grep osmosis_replication_timestamp | cut -d"=" -f2`
  osm_data_date=${osm_data_date::-1}
  echo $osm_data_date
  echo $osm_data_date > data/running
	echo "Extracting addresses from PBF"
	python3 src/download_from_osm.py
	echo "Preparing OSM data for analysis"
fi
