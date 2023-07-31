.DEFAULT_GOAL := help

help:
	@echo "Read README.md to see which commands are available"

clean: clean_rgz clean_osm

clean_rgz:
	@./src/clean_rgz.sh

clean_osm: clean_normalize_street_names clean_analysis clean_quality_assurance clean_generate_b_hn_ratio
	@echo "Removing OSM data"
	@if [ "$(AR_INCREMENTAL_UPDATE)" != "1" ]; then\
		rm -f data/osm/download/serbia.osm.pbf;\
	fi
	@if [ "$(AR_INCREMENTAL_UPDATE)" = "1" ]; then\
		if test -f "data/running"; then\
			echo "data/running.pid exists. Check if script is executing and delete before running again";\
			exit 1;\
		fi;\
	fi
	rm -f data/osm/csv/*
	rm -f data/osm/addresses.csv

clean_normalize_street_names:
	@echo "Cleaning all normalization mappings"
	@if [ "$(AR_INCREMENTAL_UPDATE)" != "1" ]; then\
		rm -f data/mapping/mapping.csv;\
	fi

clean_analysis: clean_report
	@echo "Cleaning all analysis files"
	@if [ "$(AR_INCREMENTAL_UPDATE)" = "1" ]; then\
		if test -f "data/running"; then\
			echo "data/running.pid exists. Check if script is executing and delete before running again";\
			exit 1;\
		fi;\
	fi
	rm -f data/analysis/*

clean_quality_assurance: clean_report
	@echo "Cleaning QA files"
	@if [ "$(AR_INCREMENTAL_UPDATE)" != "1" ]; then\
		rm -f data/qa/duplicated_refs.json;\
		rm -f data/qa/addresses_in_buildings_per_opstina.csv;\
		rm -f data/qa/osm_import_qa.csv;\
		rm -f data/qa/unaccounted_osm_addresses.csv;\
	fi

clean_generate_b_hn_ratio: clean_report
	@echo "Cleaning building housenumber ratio"
	@if [ "$(AR_INCREMENTAL_UPDATE)" != "1" ]; then\
		rm -f data/b-hn/building_housenumber_per_naselje.csv;\
	fi

clean_report:
	@echo "Cleaning all files from report"
	@if [ "$(AR_INCREMENTAL_UPDATE)" = "1" ]; then\
		if test -f "data/running"; then\
			echo "data/running.pid exists. Check if script is executing and delete before running again";\
			exit 1;\
		fi;\
	fi
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
	@if [ "$(AR_INCREMENTAL_UPDATE)" != "1" ]; then\
		mkdir -p data/mapping;\
		python3 src/street_mapping.py;\
	fi

analyze: download_from_osm normalize_street_names
	@echo "Analysing"
	mkdir -p data/analysis
	ls -S data/osm/csv/*.csv | parallel --jobs 8 python3 src/create_analysis.py --opstina={/.}

quality_assurance: download_from_osm
	@echo "Doing quality assurance"
	@if [ "$(AR_INCREMENTAL_UPDATE)" != "1" ]; then\
		mkdir -p data/qa;\
		python3 src/quality_assurance.py;\
		python3 src/osm_import_qa.py;\
	fi

generate_b_hn_ratio: download_from_osm
	@echo "Generating building / housenumber ratio"
	@if [ "$(AR_INCREMENTAL_UPDATE)" != "1" ]; then\
		mkdir -p data/b-hn;\
		python3 src/generate_building_addresses_ratio.py;\
	fi

report: analyze quality_assurance generate_b_hn_ratio
	@echo "Generating report"
	mkdir -p data/report
	@if [ "$(AR_INCREMENTAL_UPDATE)" = "1" ]; then\
		mkdir -p data/report/rt;\
	else\
		mkdir -p data/report/opstine;\
		mkdir -p data/report/b-hn;\
	fi
	python3 src/create_report.py
	@if [ "$(AR_INCREMENTAL_UPDATE)" != "1" ]; then\
		python3 src/create_report_qa.py;\
	fi

upload_report: report
	echo "Uploading report"
	@if [ "$(AR_INCREMENTAL_UPDATE)" != "1" ]; then\
		echo "full update";\
		./src/upload_report.sh;\
	fi
	@if [ "$(AR_INCREMENTAL_UPDATE)" = "1" ]; then\
	    echo "incremental update";\
	    ./src/upload_rt_report.sh;\
	fi
