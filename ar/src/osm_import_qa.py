# -*- coding: utf-8 -*-

import argparse
import os

import geopandas as gpd
import pandas as pd
from shapely import wkt

from common import normalize_name, normalize_name_latin, cyr2lat, load_mappings


def do_analysis(data_path, street_mappings):
    qa_path = os.path.join(data_path, 'qa')

    if os.path.exists(os.path.join(qa_path, 'osm_import_qa.csv')):
        print(f"    Skipping calculating imported address QA, data/qa/osm_import_qa.csv already exists")
        return

    input_osm_file = os.path.join(data_path, 'osm/addresses.csv')
    if not os.path.exists(input_osm_file):
        print(f"    Missing file {input_osm_file}, cannot load OSM data")
        return

    input_rgz_file = os.path.join(data_path, 'rgz/addresses.csv')
    if not os.path.exists(input_rgz_file):
        print(f"    Missing file {input_rgz_file}, cannot load RGZ addresses")
        return

    print("    Loading OSM addresses...", end='')
    df_osm = pd.read_csv(input_osm_file, dtype='unicode')
    df_osm = df_osm[pd.notna(df_osm['ref:RS:kucni_broj'])]
    df_osm['osm_geometry2'] = df_osm.osm_geometry.apply(wkt.loads)
    gdf_osm = gpd.GeoDataFrame(df_osm, geometry='osm_geometry2', crs="EPSG:4326")
    gdf_osm.drop(['ref:RS:ulica', 'osm_country', 'osm_city', 'osm_postcode', 'tags'], inplace=True, axis=1)
    gdf_osm.to_crs("EPSG:32634", inplace=True)
    gdf_osm['osm_geometry'] = gdf_osm.osm_geometry2
    gdf_osm['osm_street_norm'] = gdf_osm.osm_street.apply(normalize_name)
    gdf_osm['osm_housenumber_norm'] = gdf_osm.osm_housenumber.apply(lambda x: normalize_name_latin(x))
    gdf_osm.sindex
    print(f"found {len(gdf_osm)} addresses in OSM with ref:RS:kucni_broj")

    print("    Loading RGZ addresses...", end='')
    df_rgz = pd.read_csv(input_rgz_file, dtype={'rgz_kucni_broj_id': str})
    df_rgz['rgz_geometry'] = df_rgz.rgz_geometry.apply(wkt.loads)
    gdf_rgz = gpd.GeoDataFrame(df_rgz, geometry='rgz_geometry', crs="EPSG:4326")
    gdf_rgz.to_crs("EPSG:32634", inplace=True)
    gdf_rgz.drop(['rgz_opstina_mb', 'rgz_opstina_mb', 'rgz_naselje_mb', 'rgz_naselje'], inplace=True, axis=1)
    gdf_rgz['rgz_opstina'] = gdf_rgz['rgz_opstina'].apply(lambda x: cyr2lat(x))
    gdf_rgz['rgz_ulica_proper'] = gdf_rgz['rgz_ulica'].apply(lambda x: street_mappings[x])
    gdf_rgz['rgz_ulica_norm'] = gdf_rgz.rgz_ulica_proper.apply(normalize_name)
    gdf_rgz['rgz_kucni_broj_norm'] = gdf_rgz.rgz_kucni_broj.apply(lambda x: normalize_name_latin(x))
    gdf_rgz.sindex
    print(f"found {len(gdf_rgz)} addresses in RGZ")

    print("    Joining OSM and RGZ addresses...", end='')
    joined = pd.merge(gdf_osm, gdf_rgz, how='left', left_on='ref:RS:kucni_broj', right_on='rgz_kucni_broj_id')
    joined['distance'] = joined.osm_geometry.distance(joined.rgz_geometry)
    joined['street_perfect_match'] = joined[['rgz_ulica_proper', 'osm_street']].apply(lambda x: x['rgz_ulica_proper'] == x['osm_street'], axis=1)
    joined['street_partial_match'] = joined[['rgz_ulica_norm', 'osm_street_norm']].apply(lambda x: x['rgz_ulica_norm'] == x['osm_street_norm'], axis=1)
    joined['housenumber_perfect_match'] = joined[['rgz_kucni_broj_norm', 'osm_housenumber']].apply(lambda x: x['rgz_kucni_broj_norm'] == x['osm_housenumber'], axis=1)
    joined['housenumber_partial_match'] = joined[['rgz_kucni_broj_norm', 'osm_housenumber_norm']].apply(lambda x: x['rgz_kucni_broj_norm'] == x['osm_housenumber_norm'], axis=1)
    print("done")

    print("    Writing data/qa/osm_import_qa.csv...", end='')
    joined.to_crs("EPSG:4326", inplace=True)
    joined.set_geometry('rgz_geometry', inplace=True)
    joined.to_crs("EPSG:4326", inplace=True)

    filtered_addresses = joined[
        pd.isna(joined.rgz_ulica_mb) |
        (joined['distance'] > 50) |
        #~joined.street_perfect_match |
        #~joined.street_partial_match |
        ~joined.housenumber_perfect_match |
        ~joined.housenumber_partial_match
    ]
    filtered_addresses.sort_values(['rgz_opstina', 'rgz_ulica', 'rgz_kucni_broj', 'osm_id'], inplace=True)
    pd.DataFrame(filtered_addresses).to_csv(os.path.join(qa_path, 'osm_import_qa.csv'), index=False)
    print(f"done")


def main():
    cwd = os.getcwd()
    data_path = os.path.join(cwd, 'data/')

    print("Loading normalized street names mapping")
    street_mappings = load_mappings(data_path)

    do_analysis(data_path, street_mappings)


if __name__ == '__main__':
    main()
