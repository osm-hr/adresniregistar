.DEFAULT_GOAL := help

help:
	@echo "Read README.md to see which commands are available"

clean: clean_rgz clean_osm

clean_rgz:
	@echo "Removing RGZ data"
	rm -f data/rgz/download/*
	rm -f data/rgz/csv/*
	rm -f data/rgz/addresses.csv

clean_osm: clean_normalize_street_names clean_analysis
	@echo "Removing OSM data"
	rm -f data/osm/download/serbia.osm.pbf
	rm -f data/osm/csv/*
	rm -f data/osm/addresses.csv

clean_normalize_street_names:
	@echo "Cleaning all normalization mappings"
	rm -f data/mapping/mapping.csv

clean_analysis: clean_report
	@echo "Cleaning all analysis files"
	rm -f data/analysis/*

clean_quality_assurance: clean_report
	@echo "Cleaning QA files"
	rm -f data/qa/duplicate_refs.json

clean_report:
	@echo "Cleaning all files from report"
	rm -rf data/report/*
	rm -f data/report.tar.gz

download_from_rgz:
	@echo "Download housenumbers from RGZ"
	mkdir -p data/rgz/download
	python3 src/download_from_rgz.py
	@echo "Prepare RGZ data for analysis"
	python3 src/prepare_rgz_data.py
	@echo "Created data/rgz/addresses.csv"

download_from_osm:
	@echo "Download Serbia PBF from geofabrik"
	mkdir -p data/osm/download
	test -f data/osm/download/serbia.osm.pbf || wget http://download.geofabrik.de/europe/serbia-latest.osm.pbf -O data/osm/download/serbia.osm.pbf -q --show-progress
	@echo "Extracting addresses from PBF"
	python3 src/download_from_osm.py
	@echo "Preparing OSM data for analysis"
	mkdir -p data/osm/csv
	python3 src/prepare_osm_data.py

normalize_street_names:
	@echo "Normalizing street names"
	mkdir -p data/mapping
	python3 src/street_mapping.py

analyze: download_from_osm normalize_street_names
	@echo "Analysing"
	mkdir -p data/analysis
	python3 src/create_analysis.py

quality_assurance: download_from_osm
	@echo "Doing quality assurance"
	mkdir -p data/qa
	python3 src/quality_assurance.py

report: analyze quality_assurance
	@echo "Generating report"
	mkdir -p data/report
	mkdir -p data/report/opstine
	python3 src/create_report.py

upload_report: report
	@./src/upload_report.sh