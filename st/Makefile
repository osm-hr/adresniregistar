.DEFAULT_GOAL := help

help:
	@echo "Read README.md to see which commands are available"

clean: clean_rgz clean_osm

clean_rgz:
	@./src/clean_rgz.sh

clean_osm: clean_analysis clean_quality_assurance
	@echo "Removing OSM data"
	rm -f data/osm/download/serbia.osm.pbf
	rm -f data/osm/csv/*
	rm -f data/osm/streets.csv

clean_analysis: clean_report
	@echo "Cleaning all analysis files"
	rm -f data/analysis/*

clean_quality_assurance: clean_report
	@echo "Cleaning QA files"
	rm -f data/qa/wrong_street_names.csv

clean_report:
	@echo "Cleaning all files from report"
	rm -rf data/report/*
	rm -f data/report.tar.gz

download_from_rgz:
	@echo "Download streets from RGZ"
	mkdir -p data/rgz/download
	python3 src/download_st_from_rgz.py
	@echo "Prepare RGZ data for analysis"
	python3 src/prepare_rgz_street_data.py.py
	@echo "Created data/rgz/streets.csv"

download_from_osm:
	@echo "Download OSM data"
	@./src/download_st_from_osm.sh
	@echo "Preparing OSM data for analysis"
	mkdir -p data/osm/csv
	python3 src/prepare_osm_st_data.py

analyze: download_from_osm
	@echo "Analysing"
	mkdir -p data/analysis
	ls -S data/osm/csv/*.csv | parallel --jobs 8 python3 src/create_st_analysis.py --opstina={/.}

quality_assurance: analyze
	@echo "Doing quality assurance"
	mkdir -p data/qa
	python3 src/qa_wrong_names.py

report: quality_assurance
	@echo "Generating report"
	mkdir -p data/report
	mkdir -p data/report/opstine
	mkdir -p data/report/b-hn
	mkdir -p data/report/removed_addresses
	python3 src/create_st_report.py
	python3 src/create_st_qa_report.py

upload_report: report
	echo "Uploading report"
	@./src/upload_st_report.sh
