# -*- coding: utf-8 -*-

import os
import pandas as pd
import geopandas as gpd
from shapely import wkt
import Levenshtein
import math

from common import normalize_name


def calculate_housenumber_diff(housenumber_rgz, housenumber_osm):
    if type(housenumber_osm) == float and math.isnan(housenumber_osm):
        return 0
    housenumber_rgz_number, housenumber_rgz_letter = '', ''
    housenumber_osm_number, housenumber_osm_letter = '', ''
    for c in housenumber_rgz:
        if c.isnumeric():
            housenumber_rgz_number += c
        else:
            housenumber_rgz_letter += c
    for c in housenumber_osm:
        if c.isnumeric():
            housenumber_osm_number += c
        else:
            housenumber_osm_letter += c

    housenumber_rgz_number = int(housenumber_rgz_number) if housenumber_rgz_number != '' else 0
    housenumber_osm_number = int(housenumber_osm_number) if housenumber_osm_number != '' else 0
    diff = math.fabs(housenumber_rgz_number - housenumber_osm_number)
    return 0.9 * max(0, (5-diff)/5) + 0.1 * (1 if housenumber_rgz_letter == housenumber_osm_letter else 0)


def calculate_score(street_rgz, housenumber_rgz, street_osm, housenumber_osm, distance):
    if type(street_osm) == float and math.isnan(street_osm):
        street_diff = 0
    else:
        street_diff = Levenshtein.ratio(street_rgz, street_osm)
    housenumber_diff = calculate_housenumber_diff(housenumber_rgz, housenumber_osm)
    if type(distance) == float and math.isnan(distance):
        distance_diff = 0
    else:
        if distance > 500:
            distance = 500
        if distance < 0:
            distance = 0
        distance_diff = math.pow((500 - distance) / 500.0, 2)

    return 0.33 * street_diff + 0.33 * housenumber_diff + 0.33 * distance_diff


def do_analysis(opstina, data_path):
    if os.path.exists(os.path.join(data_path, f'analysis/{opstina}.csv')):
        return

    input_osm_file = os.path.join(data_path, f'osm/csv/{opstina}.csv')
    if not os.path.exists(input_osm_file):
        print(f"    Missing file {input_osm_file}, cannot process opstina {opstina}")
        return

    input_rgz_file = os.path.join(data_path, f'rgz/csv/{opstina}.csv')
    if not os.path.exists(input_rgz_file):
        print(f"    Missing file {input_rgz_file}, cannot process opstina {opstina}")
        return

    print(f"    Loading OSM addresses in {opstina}")
    df_osm = pd.read_csv(input_osm_file)
    df_osm['osm_geometry2'] = df_osm.osm_geometry.apply(wkt.loads)
    gdf_osm = gpd.GeoDataFrame(df_osm, geometry='osm_geometry2', crs="EPSG:4326")
    gdf_osm.drop(['osm_country', 'osm_city', 'osm_postcode'], inplace=True, axis=1)
    gdf_osm.to_crs("EPSG:32634", inplace=True)
    gdf_osm['osm_geometry'] = gdf_osm.osm_geometry2
    gdf_osm['osm_street_norm'] = gdf_osm.osm_street.apply(normalize_name)
    gdf_osm['osm_housenumber_norm'] = gdf_osm.osm_housenumber.apply(normalize_name)
    gdf_osm.sindex

    print(f"    Loading RGZ addresses in {opstina}")
    df_rgz = pd.read_csv(input_rgz_file)
    df_rgz['rgz_geometry'] = df_rgz.rgz_geometry.apply(wkt.loads)
    gdf_rgz = gpd.GeoDataFrame(df_rgz, geometry='rgz_geometry', crs="EPSG:4326")
    gdf_rgz.to_crs("EPSG:32634", inplace=True)
    gdf_rgz.drop(['rgz_opstina_mb', 'rgz_opstina'], inplace=True, axis=1)
    gdf_rgz['rgz_ulica_norm'] = gdf_rgz.rgz_ulica.apply(normalize_name)
    gdf_rgz['rgz_kucni_broj_norm'] = gdf_rgz.rgz_kucni_broj.apply(normalize_name)
    gdf_rgz.sindex

    print(f"    Buffering RGZ addresses for 200m in {opstina}")
    gdf_rgz['rgz_buffered_geometry'] = gdf_rgz.rgz_geometry.buffer(distance=200)
    gdf_rgz.set_geometry('rgz_buffered_geometry', inplace=True)
    gdf_rgz.sindex

    print(f"    Joining addresses in RGZ and OSM in {opstina}")
    joined = gdf_rgz.sjoin(gdf_osm, how='left', predicate='intersects')
    joined['distance'] = joined.rgz_geometry.distance(joined.osm_geometry)
    joined.sindex

    print(f"    Calculating score and matches for addresses in {opstina}")
    joined['score'] = joined.apply(lambda row: calculate_score(
        row['rgz_ulica_norm'], row['rgz_kucni_broj_norm'],
        row['osm_street_norm'], row['osm_housenumber_norm'], row['distance']), axis=1)
    joined['matching'] = joined.apply(lambda row:
        row['rgz_ulica_norm'] == row['osm_street_norm'] and row['rgz_kucni_broj_norm'] == row['osm_housenumber_norm'], axis=1)

    # TODO: try to somehow exclude address that are already conflated or part of perfect match
    print(f"    Finding best matches for addresses in {opstina}")
    joined.sort_values(['rgz_kucni_broj_id', 'matching', 'score', 'osm_id'], ascending=[True, False, False, False], inplace=True)
    joined['rank'] = 1
    joined['conflated'] = False  # TODO: actually calculate this
    joined['rank'] = joined.groupby(['rgz_kucni_broj_id'])['rank'].cumsum()
    joined = joined[joined['rank'] == 1]

    print("    Saving analysis")
    joined.drop(['index_right', 'rgz_ulica_norm', 'rgz_kucni_broj_norm', 'rgz_buffered_geometry', 'osm_street_norm', 'osm_housenumber_norm', 'rank'], inplace=True, axis=1)
    joined.set_geometry('osm_geometry', inplace=True)
    joined.to_crs("EPSG:4326", inplace=True)
    joined.set_geometry('rgz_geometry', inplace=True)
    joined.to_crs("EPSG:4326", inplace=True)
    #joined.assign(rgz_geometry=joined["rgz_geometry"].apply(lambda p: p.wkt))
    pd.DataFrame(joined).to_csv(os.path.join(data_path, f'analysis/{opstina}.csv'), index=False)


def main():
    cwd = os.getcwd()
    data_path = os.path.join(cwd, 'data/')
    rgz_csv_path = os.path.join(data_path, 'rgz/csv')
    total_csvs = len(os.listdir(rgz_csv_path))
    for i, file in enumerate(os.listdir(rgz_csv_path)):
        if not file.endswith(".csv"):
            continue
        opstina = file[:-4]
        print(f"{i + 1}/{total_csvs} Processing {opstina}")
        do_analysis(opstina, data_path)


if __name__ == '__main__':
    main()
