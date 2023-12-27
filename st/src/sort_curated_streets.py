# -*- coding: utf-8 -*-

import argparse
import csv
import os

from street_mapping import load_curated


def main(input_curated_streets_file_path, output_curated_streets_file_path):
    if not os.path.exists(input_curated_streets_file_path):
        print(f"File {input_curated_streets_file_path} do not exist. Quitting")
        return
    if os.path.exists(output_curated_streets_file_path):
        print(f"File {output_curated_streets_file_path} already exist, remove to continue. Quitting")
        return

    curated_streets = load_curated(input_curated_streets_file_path)
    with open(output_curated_streets_file_path, 'w', encoding="utf-8") as curated_streets_csv_file:
        writer = csv.DictWriter(
            curated_streets_csv_file,
            fieldnames=['rgz_name', 'name'])
        writer.writeheader()
        curated_streets_sorted = sorted(curated_streets)
        for rgz_name in curated_streets_sorted:
            if rgz_name == '':
                raise Exception()
            writer.writerow({
                'rgz_name': rgz_name,
                'name': curated_streets[rgz_name]
            })


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='prepare_rgz_data.py - Extract RGZ .zip files and creates addresses.csv')
    parser.add_argument('--input-curated-streets', default=None, required=True, help='Input CSV file with curated streets')
    parser.add_argument('--output-curated-streets', default=None, required=True, help='Output CSV file with curated streets')
    args = parser.parse_args()
    main(args.input_curated_streets, args.output_curated_streets)
