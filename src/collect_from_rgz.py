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


def load_opstina_csv(opstina_csv_path):
    results = []
    with open(opstina_csv_path) as opstina_csv_file:
        reader = csv.DictReader(opstina_csv_file)

        for row in reader:
            try:
                geometry = reproject_wkt(row['geometry'])
            except shapely.errors.WKTReadingError:
                print(f"Error reprojecting {row['ulica_ime']} {row['kucni_broj']} in {row['naselje_ime']} ({row['opstina_ime']}), skipping")
                continue

            results.append(
                {'kucni_broj_id': row['kucni_broj_id'],
                 'kucni_broj': row['kucni_broj'],
                 'vrsta_stanja': row['vrsta_stanja'],
                 'created': row['created'],
                 'retired': row['retired'],
                 'opstina_maticni_broj': row['opstina_maticni_broj'],
                 'opstina_ime': row['opstina_ime'],
                 'naselje_maticni_broj': row['naselje_maticni_broj'],
                 'naselje_ime': row['naselje_ime'],
                 'ulica_maticni_broj': row['ulica_maticni_broj'],
                 'ulica_ime': row['ulica_ime'],
                 'geometry': geometry
                 })
    return results


def main():
    cwd = os.getcwd()
    download_path = os.path.join(cwd, 'data/rgz_opstine/download')
    collect_path = os.path.join(cwd, 'data/rgz_opstine')
    all_addresses = []
    total_zips = len(os.listdir(download_path))
    for i, file in enumerate(os.listdir(download_path)):
        if not file.endswith(".zip"):
            continue
        opstina = file[:-4]
        print(f"{i}/{total_zips} Processing {opstina}")
        with zipfile.ZipFile(os.path.join(download_path, file), 'r') as zip_ref:
            zip_ref.extract(opstina + ".csv", collect_path)
        opstina_csv_file = os.path.join(collect_path, opstina + ".csv")
        all_addresses += load_opstina_csv(opstina_csv_file)
        os.remove(opstina_csv_file)

    print("Collecting all addresses")
    all_addresses_path = os.path.join(collect_path, 'all_addresses.csv')
    with open(all_addresses_path, 'w') as all_addresses_csv:
        writer = csv.DictWriter(
            all_addresses_csv, fieldnames=['kucni_broj_id', 'opstina_maticni_broj', 'opstina_ime',
                                           'naselje_maticni_broj', 'opstina_ime', 'naselje_maticni_broj', 'naselje_ime',
                                           'ulica_maticni_broj', 'ulica_ime', 'kucni_broj', 'vrsta_stanja', 'created',
                                           'retired', 'geometry'])
        writer.writeheader()
        for address in all_addresses:
            writer.writerow(address)
    print(f"All {len(all_addresses)} addresses written to all_addresses.csv")


if __name__ == '__main__':
    main()
