.DEFAULT_GOAL := help

help:
	@echo "Read README.md to see which commands are available"

clean:
	@echo "Cleaning all"
	rm -r data/rgz/download/*
	rm -r data/rgz/csv/*
	rm data/rgz/addresses.csv
	rm data/osm/download/serbia.osm.pbf
	rm data/osm/addresses.csv

download_from_rgz:
	@echo "Download housenumbers from RGZ"
	mkdir -p data/rgz/download
	python3 src/download_from_rgz.py
	@echo "Prepare RGZ data for analysis"
	python src/prepare_rgz_data.py
	@echo "Created data/rgz/addresses.csv"

download_from_osm:
	@echo "Download Serbia PBF from geofabrik"
	mkdir -p data/osm/download
	wget http://download.geofabrik.de/europe/serbia-latest.osm.pbf -O data/osm/download/serbia.osm.pbf -q --show-progress
	@echo "Extracting addresses from PBF"
	python3 src/download_from_osm.py
	@echo "Preparing OSM data for analysis"
	mkdir -p data/osm/csv
	python3 src/prepare_osm_data.py

analyze:
	@echo "Analysing"
	mkdir -p data/analysis
	python3 src/create_analysis.py

report:
	@echo "Generating report"
	mkdir -p data/report
	mkdir -p data/report/opstine
	python3 src/create_report.py