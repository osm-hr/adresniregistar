# -*- coding: utf-8 -*-

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

        for row in reader:
            try:
                geometry = reproject_wkt(row['geometry'])
            except shapely.errors.WKTReadingError:
                print(f"Error reprojecting {row['ulica_ime']} {row['kucni_broj']} in {row['naselje_ime']} ({row['opstina_ime']}), skipping")
                continue

            if row['vrsta_stanja'] != 'АКТИВАН':
                print(f"Skipped {row['ulica_ime']} {row['rgz_kucni_broj']} since it is in state {row['vrsta_stanja']}")
                continue
            if row['retired'] != '':
                print(f"Skipped {row['ulica_ime']} {row['rgz_kucni_broj']} since it is retired as {row['retired']}")
                continue
            if row['opstina_ime_lat'] != opstina:
                print(f"Unexpected opstina {row['opstina_ime']} during processing of opstina {opstina}")
                continue

            results.append(
                {'rgz_kucni_broj_id': row['kucni_broj_id'],
                 'rgz_kucni_broj': row['kucni_broj'],
                 'rgz_opstina_mb': row['opstina_maticni_broj'],
                 'rgz_opstina': row['opstina_ime'],
                 'rgz_naselje_mb': row['naselje_maticni_broj'],
                 'rgz_naselje': row['naselje_ime'],
                 'rgz_ulica_mb': row['ulica_maticni_broj'],
                 'rgz_ulica': row['ulica_ime'],
                 'rgz_geometry': geometry
                 })
    return results


def main():
    cwd = os.getcwd()
    rgz_path = os.path.join(cwd, 'data/rgz')
    download_path = os.path.join(rgz_path, 'download/')
    collect_path = os.path.join(rgz_path, 'csv/')
    all_addresses = []
    total_zips = len(os.listdir(download_path))
    for i, file in enumerate(os.listdir(download_path)):
        if not file.endswith(".zip"):
            continue
        opstina = file[:-4]
        print(f"{i+1}/{total_zips} Processing {opstina}")
        with zipfile.ZipFile(os.path.join(download_path, file), 'r') as zip_ref:
            zip_ref.extract(opstina + ".csv", rgz_path)
        temp_opstina_csv_file = os.path.join(rgz_path, opstina + ".csv")
        opstina_addresses = load_opstina_csv(opstina, temp_opstina_csv_file)
        all_addresses += opstina_addresses
        os.remove(temp_opstina_csv_file)

        with open(os.path.join(collect_path, opstina + ".csv"), 'w') as opstina_addresses_csv:
            writer = csv.DictWriter(
                opstina_addresses_csv, fieldnames=['rgz_kucni_broj_id', 'rgz_opstina_mb', 'rgz_opstina',
                                               'rgz_naselje_mb', 'rgz_naselje', 'rgz_ulica_mb', 'rgz_ulica',
                                               'rgz_kucni_broj', 'rgz_geometry'])
            writer.writeheader()
            for address in opstina_addresses:
                writer.writerow(address)

    print("Collecting all addresses")
    all_addresses_path = os.path.join(rgz_path, 'addresses.csv')
    with open(all_addresses_path, 'w') as all_addresses_csv:
        writer = csv.DictWriter(
            all_addresses_csv, fieldnames=['rgz_kucni_broj_id', 'rgz_opstina_mb', 'rgz_opstina',
                                           'rgz_naselje_mb', 'rgz_naselje', 'rgz_ulica_mb', 'rgz_ulica',
                                           'rgz_kucni_broj', 'rgz_geometry'])
        writer.writeheader()
        for address in all_addresses:
            writer.writerow(address)
    print(f"All {len(all_addresses)} addresses written to data/rgz/addresses.csv")


if __name__ == '__main__':
    main()
