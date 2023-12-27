# -*- coding: utf-8 -*-

import argparse
import csv
import os
import sys
import zipfile

import pyproj
import shapely.errors
from shapely import wkt
from shapely.ops import transform

csv.field_size_limit(sys.maxsize)

wgs84 = pyproj.CRS('EPSG:4326')
utm = pyproj.CRS('EPSG:32634')
project = pyproj.Transformer.from_crs(utm, wgs84, always_xy=True).transform


def reproject_wkt(wkt_text):
    wkt_obj = wkt.loads(wkt_text)
    return transform(project, wkt_obj)


def load_opstina_csv(opstina, opstina_csv_path):
    results = []
    with open(opstina_csv_path) as opstina_csv_file:
        reader = csv.DictReader(opstina_csv_file)
        if 'kucni_broj_id' in reader.fieldnames:
            print(f"File {opstina_csv_path} have addresses, not streets, quitting")
            raise Exception()
        for row in reader:
            try:
                geometry = reproject_wkt(row['geometry'])
            except shapely.errors.WKTReadingError:
                print(f"Error reprojecting {row['ulica_ime']} in {row['naselje_ime']} ({row['opstina_ime']}), skipping")
                continue

            if row['opstina_ime_lat'] != opstina:
                print(f"Unexpected opstina {row['opstina_ime']} during processing of opstina {opstina}")
                continue

            results.append(
                {'rgz_opstina': row['opstina_ime'],
                 'rgz_naselje_mb': row['naselje_maticni_broj'],
                 'rgz_naselje': row['naselje_ime'],
                 'rgz_ulica_mb': row['ulica_maticni_broj'],
                 'rgz_ulica': row['ulica_ime'],
                 'rgz_geometry': geometry
                 })
    return results


def main(output_csv_file_path, output_csv_folder):
    cwd = os.getcwd()
    rgz_path = os.path.join(cwd, 'data/rgz')
    download_path = os.path.join(rgz_path, 'download/')

    need_address_collection = True
    if os.path.exists(output_csv_file_path):
        print(f"File {output_csv_file_path} already exist, remove it to continue. Quitting")
        return

    all_streets = []
    total_zips = len(os.listdir(download_path))
    for i, file in enumerate(os.listdir(download_path)):
        if not file.endswith(".zip"):
            continue
        opstina = file[:-4]
        opstina_csv_path = os.path.join(output_csv_folder, opstina + ".csv")

        print(f"{i+1}/{total_zips} Processing {opstina}... ", end='')
        if os.path.exists(opstina_csv_path) and not need_address_collection:
            print(f"skipping, file {opstina_csv_path} already exists")
            continue

        with zipfile.ZipFile(os.path.join(download_path, file), 'r') as zip_ref:
            zip_ref.extract(opstina + ".csv", rgz_path)
        temp_opstina_csv_file = os.path.join(rgz_path, opstina + ".csv")
        with open(temp_opstina_csv_file) as opstina_csv_file:
            reader = csv.DictReader(opstina_csv_file)
            if 'kucni_broj_id' in reader.fieldnames:
                os.remove(os.path.join(download_path, file))
                print(f"Removed file {file} as it contained addresses and not streets")
                continue
        opstina_streets = load_opstina_csv(opstina, temp_opstina_csv_file)
        all_streets += opstina_streets
        os.remove(temp_opstina_csv_file)

        if os.path.exists(opstina_csv_path):
            print(f"skipping, file data/rgz/csv/{opstina}.csv already exists")
            continue

        with open(opstina_csv_path, 'w') as opstina_streets_csv:
            writer = csv.DictWriter(
                opstina_streets_csv, fieldnames=['rgz_opstina', 'rgz_naselje_mb', 'rgz_naselje', 'rgz_ulica_mb', 'rgz_ulica', 'rgz_geometry'])
            writer.writeheader()
            for address in opstina_streets:
                writer.writerow(address)
        print("OK")

    print("Collecting all streets...", end='')

    with open(output_csv_file_path, 'w') as all_streets_csv:
        writer = csv.DictWriter(
            all_streets_csv, fieldnames=['rgz_kucni_broj_id', 'rgz_opstina_mb', 'rgz_opstina',
                                           'rgz_naselje_mb', 'rgz_naselje', 'rgz_ulica_mb', 'rgz_ulica',
                                           'rgz_kucni_broj', 'rgz_geometry'])
        writer.writeheader()
        for address in all_streets:
            writer.writerow(address)
    print(f"OK ({len(all_streets)} streets written)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='prepare_rgz_data.py - Extract RGZ .zip files and creates addresses.csv')
    parser.add_argument('--output-csv-file', default=None, required=True, help='Output CSV file for all RGZ streets')
    parser.add_argument('--output-csv-folder', default=None, required=True, help='Output directory for RGZ streets per municipality')
    args = parser.parse_args()
    main(args.output_csv_file, args.output_csv_folder)
