.DEFAULT_GOAL := help

help:
	@echo "Read README.md to see which commands are available"

clean: clean_osm

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
		rm -f data/qa/removed_addresses.csv;\
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

clean_inspire_data:
	@echo "Cleaning Inspire data"
	rm -rf data/rgz/unzip/*
	rm -rf data/rgz/download/*
	rm -rf data/rgz/csv/*
	rm -f data/rgz/naselje.csv
	rm -f data/rgz/opstina.csv
	rm -f data/rgz/addresses.csv

download_from_osm:
	@./src/download_from_osm.sh
	@echo "Preparing OSM data for analysis"
	mkdir -p data/osm/csv
	python3 src/prepare_osm_data.py

download_inspire_data:
	mkdir -p data/rgz/unzip
	@if ./src/inspire_check_feed.sh && \
	    [ -f data/rgz/opstina.csv ] && \
	    [ -f data/rgz/naselje.csv ] && \
	    [ -f data/rgz/addresses.csv ]; then \
		echo "Inspire podaci su ažurni."; \
	else \
		$(MAKE) clean_inspire_data && \
		./src/download_inspire_data.sh && \
		python3 ./src/parse_inspire_admin_data.py --country $(COUNTRY) --admin-level opstina --input data/rgz/unzip/AdministrativeUnitOpstina.gml --output data/rgz/opstina.csv "$(INSPIRE_ADMIN_LEVEL_1_NAME)" && \
		if [ "$(COUNTRY)" = "croatia" ]; then \
			python3 ./src/parse_inspire_admin_data.py --country $(COUNTRY) --admin-level naselje --input data/rgz/unzip/AdministrativeUnitNaselje.gml --output data/rgz/naselja.csv "$(INSPIRE_ADMIN_LEVEL_2_NAME)"; \
		fi && \
		duckdb -csv < src/inspire-consolidate_addresses-$(COUNTRY).sql > data/rgz/addresses.csv && \
		duckdb -csv < src/inspire-convert_admin_boundaries-$(COUNTRY).sql > data/rgz/naselje.csv && \
		[ "$(COUNTRY)" != "slovenia" ] || python3 ./src/generate_voronoi_borders.py && \
		python3 ./src/prepare_inspire_data.py && \
		duckdb -csv < src/fixed-street_names_list.sql > data/rgz/fixed_street_names_list.csv && \
		rm -f data/rgz/naselja.csv; \
	fi


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
		python3 src/generate_removed_addresses_qa.py;\
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
		mkdir -p data/report/removed_addresses;\
	fi
	python3 src/create_report.py
	@if [ "$(AR_INCREMENTAL_UPDATE)" != "1" ]; then\
		python3 src/create_report_qa.py;\
	fi

report_with_inspire_data: download_inspire_data report

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
