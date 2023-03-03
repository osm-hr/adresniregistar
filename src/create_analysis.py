# -*- coding: utf-8 -*-

import math
import os

import Levenshtein
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import wkt

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
    df_osm = pd.read_csv(input_osm_file, dtype={'ref:RS:ulica': object, 'ref:RS:kucni_broj': object})
    df_osm['osm_geometry2'] = df_osm.osm_geometry.apply(wkt.loads)
    gdf_osm = gpd.GeoDataFrame(df_osm, geometry='osm_geometry2', crs="EPSG:4326")
    gdf_osm.drop(['osm_country', 'osm_city', 'osm_postcode'], inplace=True, axis=1)
    gdf_osm.to_crs("EPSG:32634", inplace=True)
    gdf_osm['osm_geometry'] = gdf_osm.osm_geometry2
    gdf_osm['osm_street_norm'] = gdf_osm.osm_street.apply(normalize_name)
    gdf_osm['osm_housenumber_norm'] = gdf_osm.osm_housenumber.apply(normalize_name)
    gdf_osm.sindex

    print(f"    Loading RGZ addresses in {opstina}")
    df_rgz = pd.read_csv(input_rgz_file, dtype={'rgz_kucni_broj_id': str})
    df_rgz['rgz_geometry'] = df_rgz.rgz_geometry.apply(wkt.loads)
    gdf_rgz = gpd.GeoDataFrame(df_rgz, geometry='rgz_geometry', crs="EPSG:4326")
    gdf_rgz.to_crs("EPSG:32634", inplace=True)
    gdf_rgz.drop(['rgz_opstina_mb', 'rgz_opstina'], inplace=True, axis=1)
    gdf_rgz['rgz_ulica_norm'] = gdf_rgz.rgz_ulica.apply(normalize_name)
    gdf_rgz['rgz_kucni_broj_norm'] = gdf_rgz.rgz_kucni_broj.apply(normalize_name)
    gdf_rgz.sindex

    # First we will join RGZ and OSM on "ref:RS:kucni_broj. During this process, we calculate distance and remove extra
    # (not-needed) columns. We need to watch out if same "ref:RS:kucni_broj" exists 2 times in OSM! In this case,
    # we take closer address. We don't worry about it here, as we will have QA to report on this.
    print(f"    Joining addresses in RGZ and OSM in {opstina} by conflation (ref:RS:kucni_broj)")
    gdf_osm['osm_housenumber'] = gdf_osm['osm_housenumber'].astype('str')  # For some reason, we need to explicitely cast this to string
    gdf_rgz = gdf_rgz.merge(gdf_osm, how='left', left_on='rgz_kucni_broj_id', right_on='ref:RS:kucni_broj')
    gdf_rgz['conflated_distance'] = gdf_rgz.rgz_geometry.distance(gdf_rgz.osm_geometry)
    gdf_rgz.rename(columns={'osm_id': 'conflated_osm_id', 'osm_street': 'conflated_osm_street', 'osm_housenumber': 'conflated_osm_housenumber'}, inplace=True)
    gdf_rgz.drop(['ref:RS:kucni_broj', 'ref:RS:ulica', 'osm_geometry', 'osm_geometry2', 'osm_street_norm', 'osm_housenumber_norm'], inplace=True, axis=1)
    gdf_rgz['rank'] = 1
    gdf_rgz['rank'] = gdf_rgz.sort_values('conflated_distance').groupby('rgz_kucni_broj_id')['rank'].cumsum()
    gdf_rgz = gdf_rgz[gdf_rgz['rank'] == 1]
    gdf_rgz.drop(['rank'], inplace=True, axis=1)
    gdf_rgz.sindex

    # Now we try to find the closest matching addresses when there is no conflation.
    # For this, we first need to create 200m buffer on which we will join RGZ to OSM.
    print(f"    Buffering RGZ addresses for 200m in {opstina}")
    gdf_rgz['rgz_buffered_geometry'] = gdf_rgz.rgz_geometry.buffer(distance=200)
    gdf_rgz.set_geometry('rgz_buffered_geometry', inplace=True)
    gdf_rgz.sindex

    print(f"    Joining addresses in RGZ and OSM in {opstina}")
    gdf_osm_no_conflated = gdf_osm[gdf_osm["ref:RS:kucni_broj"].isna()]
    joined = gdf_rgz.sjoin(gdf_osm_no_conflated, how='left', predicate='intersects')
    joined['distance'] = joined.rgz_geometry.distance(joined.osm_geometry)
    joined.sindex

    # At this point we have multiple rows for each RGZ address (those are RGZ-OSM pair within 200m).
    # For each pair, we will calculate "score" of how close they are matching with name. Also calculate perfect matches.
    print(f"    Calculating score and matches for addresses in {opstina}")
    joined['score'] = joined.apply(lambda row: calculate_score(
        row['rgz_ulica_norm'], row['rgz_kucni_broj_norm'],
        row['osm_street_norm'], row['osm_housenumber_norm'], row['distance']), axis=1)
    joined['matching'] = joined.apply(lambda row:
        row['rgz_ulica_norm'] == row['osm_street_norm'] and row['rgz_kucni_broj_norm'] == row['osm_housenumber_norm'], axis=1)

    # Now that we have matching address, we should remove them from wherever else they are showing to clear things
    mathed_osm_id_series = joined[joined.matching].osm_id
    for _, osm_id in mathed_osm_id_series.iteritems():
        joined.loc[(joined.osm_id == osm_id) & (joined.matching == False), ['score']] = 0.0
        joined.loc[(joined.osm_id == osm_id) & (joined.matching == False),
                   ['index_right', 'osm_id', 'osm_street', 'osm_housenumber', 'ref:RS:ulica', 'ref:RS:kucni_broj', 'osm_geometry', 'osm_street_norm', 'osm_housenumber_norm', 'distance']] = np.nan

    # Since we might have multiple addresses from OSM associated to various RGZ addresses,
    # we should keep only one of those. It doesn't make sense to offer same OSM address for multiple RGZ addresses.
    # Sort by score and take first one, reset other.
    joined.sort_values(['osm_id', 'score'], ascending=[True, False], inplace=True)
    joined['rank'] = 1
    joined['rank'] = joined.groupby(['osm_id'])['rank'].shift().cumsum()
    joined.loc[pd.notna(joined['rank']), ['score']] = 0.0
    joined.loc[pd.notna(joined['rank']),
               ['index_right', 'osm_id', 'osm_street', 'osm_housenumber', 'ref:RS:ulica', 'ref:RS:kucni_broj',
                'osm_geometry', 'osm_street_norm', 'osm_housenumber_norm', 'distance']] = np.nan

    # Out of all these calculated pairs, we want to pick only best one. For this, we use ranking function.
    # Sort by matching and score (and osm_id to always get consistent result), and get cumulative sum rank.
    # Once we take only rank=1, we get best candidates. This is how we remove rest of all those RGZ-OSM pairs.
    # TODO: try to somehow exclude address that are already conflated or part of perfect match
    print(f"    Finding best matches for addresses in {opstina}")
    joined.sort_values(['rgz_kucni_broj_id', 'matching', 'score', 'osm_id'], ascending=[True, False, False, False], inplace=True)
    joined['rank'] = 1
    joined['rank'] = joined.groupby(['rgz_kucni_broj_id'])['rank'].cumsum()
    joined = joined[joined['rank'] == 1]
    joined.drop(['index_right', 'rgz_ulica_norm', 'rgz_kucni_broj_norm', 'rgz_buffered_geometry', 'osm_street_norm', 'osm_housenumber_norm', 'rank'], inplace=True, axis=1)

    # At the end, save CSV
    print("    Saving analysis")
    joined.set_geometry('osm_geometry', inplace=True)
    joined.to_crs("EPSG:4326", inplace=True)
    joined.set_geometry('rgz_geometry', inplace=True)
    joined.to_crs("EPSG:4326", inplace=True)
    pd.DataFrame(joined).to_csv(os.path.join(data_path, f'analysis/{opstina}.csv'), index=False)


def main():
    cwd = os.getcwd()
    data_path = os.path.join(cwd, 'data/')
    rgz_csv_path = os.path.join(data_path, 'rgz/csv')
    total_csvs = len(os.listdir(rgz_csv_path))
    for i, file in enumerate(sorted(os.listdir(rgz_csv_path))):
        if not file.endswith(".csv"):
            continue
        opstina = file[:-4]
        print(f"{i + 1}/{total_csvs} Processing {opstina}")
        do_analysis(opstina, data_path)


if __name__ == '__main__':
    main()
