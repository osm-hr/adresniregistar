.DEFAULT_GOAL := help

help:
	@echo "Pročitajte README.md da vidite koje komande su dostupne"

clean:
	@echo "Cleaning all"
	rm -r data/rgz_opstine/download/*
	rm data/rgz_opstine/all_addresses.csv
	rm data/osm/download/serbia.osm.pbf
	rm data/osm/osm_addresses.csv

download_from_rgz:
	@echo "Download housenumbers from RGZ"
	mkdir -p data/rgz_opstine/download
	python3 src/download_from_rgz.py
	python src/collect_from_rgz.py
	@echo "Created data/rgz_opstine/all_addresses.csv"

download_from_osm:
	@echo "Download Serbia PBF from geofabrik"
	mkdir -p data/osm/download
	wget http://download.geofabrik.de/europe/serbia-latest.osm.pbf -O data/osm/download/serbia.osm.pbf -q --show-progress
	python3 src/download_from_osm.py