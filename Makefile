.DEFAULT_GOAL := help

help:
	@echo "Read README.md to see which commands are available"

clean: clean_rgz clean_osm

clean_rgz:
	@./src/clean_rgz.sh

clean_osm: clean_normalize_street_names clean_analysis clean_quality_assurance
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
	rm -f data/qa/duplicated_refs.json
	rm -f data/qa/addresses_in_buildings_per_opstina.csv

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
	@./src/download_from_osm.sh
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
	ls -S data/rgz/csv/*.csv | parallel python3 src/create_analysis.py --opstina={/.}

quality_assurance: download_from_osm
	@echo "Doing quality assurance"
	mkdir -p data/qa
	python3 src/quality_assurance.py

report: analyze quality_assurance
	@echo "Generating report"
	mkdir -p data/report
	mkdir -p data/report/opstine
	python3 src/create_report.py
	python3 src/create_report_qa.py

upload_report: report
	@./src/upload_report.sh