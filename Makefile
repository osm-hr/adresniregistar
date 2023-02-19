clean:
	@echo "Cleaning all"
	rm -r data/rgz_opstine/download/*
	rm data/rgz_opstine/all_addresses.csv

download_from_rgz:
	@echo "Download housenumbers from RGZ"
	mkdir -p data/rgz_opstine/download
	python3 src/download_from_rgz.py
	python src/collect_from_rgz.py
	@echo "Created data/rgz_opstine/all_addresses.csv"
