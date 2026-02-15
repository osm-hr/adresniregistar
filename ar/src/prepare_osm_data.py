# -*- coding: utf-8 -*-

import os

import geopandas as gpd
import pandas as pd
from shapely import wkt

from common import OPSTINE_TO_SKIP
import settings


def main():
    cwd = os.getcwd()
    osm_path = os.path.join(cwd, 'data/osm')
    rgz_path = os.path.join(cwd, 'data/rgz')

    if settings.OPSTINE_DATA_TYPE.lower() == 'csv' and not os.path.exists(os.path.join(rgz_path, 'opstina.csv')):
        print("Skinite opstine.zip sa https://opendata.geosrbija.rs i otpakujte opstina.csv u data/rgz/ direktorijum")
        return

    if settings.OPSTINE_DATA_TYPE.lower() == 'geojson' and not os.path.exists(os.path.join(rgz_path, 'opstina.geojson')):
        print("Pokrenite download_from_dgu.sh skriptu")
        return

    print("Load opstine geometries")
    if settings.OPSTINE_DATA_TYPE.lower() == 'csv':
        df_opstine = pd.read_csv(os.path.join(rgz_path, 'opstina.csv'), dtype='unicode')
        df_opstine['geometry'] = df_opstine.geometry.apply(wkt.loads)
        gdf_opstine = gpd.GeoDataFrame(df_opstine, geometry='geometry', crs="EPSG:32634")
    elif settings.OPSTINE_DATA_TYPE.lower() == 'geojson':
        gdf_opstine = gpd.read_file(os.path.join(rgz_path, 'opstina.geojson'))
        gdf_opstine.rename(columns={'nationalCode': 'opstina_maticni_broj', 'text': 'opstina_imel'}, inplace=True)
    else:
        raise ValueError(f"Unsupported OPSTINE_DATA_TYPE: {settings.OPSTINE_DATA_TYPE}")
    gdf_opstine.to_crs("EPSG:4326", inplace=True)
    gdf_opstine.sindex
    if settings.ENHANCE_WITH_NASELJA.lower() == 'true':

        df_naselja = pd.read_csv(os.path.join(rgz_path, 'naselje.csv'), dtype='unicode')
        df_naselja['geometry'] = df_naselja.wkt.apply(wkt.loads)
        gdf_naselja = gpd.GeoDataFrame(df_naselja, geometry='geometry', crs="EPSG:32634")
        gdf_naselja.to_crs("EPSG:4326", inplace=True)
        gdf_naselja.sindex

        gdf_naselja = gdf_naselja.groupby('opstina_maticni_broj').agg({
            'geometry': lambda x: x.unary_union
        }).reset_index()

        gdf_opstine = gdf_opstine.merge(gdf_naselja, on='opstina_maticni_broj', suffixes=('', '_naselja'))
        gdf_opstine['geometry'] = gdf_opstine.apply(lambda row: row['geometry'].union(row['geometry_naselja']), axis=1)
        gdf_opstine.drop(['geometry_naselja'], inplace=True, axis=1)
    all_opstina_exist = True
    for i, row in gdf_opstine.iterrows():
        opstina = row['opstina_imel']
        if opstina in OPSTINE_TO_SKIP:
            continue
        csv_file_path = os.path.join(osm_path, 'csv', f"{opstina}.csv")
        if not os.path.exists(csv_file_path):
            all_opstina_exist = False
            break
    if all_opstina_exist:
        print("Skipping all opstina as they all exist")
        return

    print("Load all OSM addresses")
    df_addresses = pd.read_csv(os.path.join(osm_path, 'addresses.csv'), dtype={'ref:RS:ulica': 'string', 'ref:RS:kucni_broj': 'string', 'osm_postcode': 'string'})
    df_addresses['osm_geometry'] = df_addresses.osm_geometry.apply(wkt.loads)
    gdf_addresses = gpd.GeoDataFrame(df_addresses, geometry='osm_geometry', crs="EPSG:4326")
    gdf_addresses.sindex

    print("Finding opstina for each OSM address")
    addresses_with_opstina = gdf_addresses.sjoin(gdf_opstine, how='inner', predicate='intersects')
    addresses_with_opstina['ref:RS:ulica'] = addresses_with_opstina['ref:RS:ulica'].astype('str')

    for i, row in gdf_opstine.iterrows():
        opstina = row['opstina_imel']
        csv_filename = f"{opstina}.csv"
        csv_file_path = os.path.join(osm_path, 'csv', csv_filename)
        if os.path.exists(csv_file_path):
            print(f"Skipping {opstina} as data/osm/csv/{csv_filename} already exists")
            continue

        if opstina in OPSTINE_TO_SKIP:
            continue
        print(f"{i+1}/{len(gdf_opstine)} Processing {opstina}")
        addresses_in_opstina = addresses_with_opstina[addresses_with_opstina['opstina_imel'] == opstina].copy()
        addresses_in_opstina.drop(['index_right', 'opstina_maticni_broj', 'opstina_ime', 'opstina_imel',
                   'opstina_povrsina', 'okrug_sifra'], inplace=True, axis=1, errors='ignore')

        if len(addresses_in_opstina) == 0:
            print(f"{opstina} doesn't seem to have any address")
            continue

        pd.DataFrame(addresses_in_opstina).to_csv(csv_file_path, index=False)


if __name__ == '__main__':
    main()
