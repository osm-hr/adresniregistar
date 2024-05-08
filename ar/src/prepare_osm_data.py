# -*- coding: utf-8 -*-

import os

import geopandas as gpd
import pandas as pd
from shapely import wkt

from common import OPSTINE_TO_SKIP


def main():
    cwd = os.getcwd()
    osm_path = os.path.join(cwd, 'data/osm')
    rgz_path = os.path.join(cwd, 'data/rgz')

    if not os.path.exists(os.path.join(rgz_path, 'opstina.csv')):
        print("Skinite opstine.zip sa https://opendata.geosrbija.rs i otpakujte opstina.csv u data/rgz/ direktorijum")
        return

    print("Load opstine geometries")
    df_opstine = pd.read_csv(os.path.join(rgz_path, 'opstina.csv'), dtype='unicode')
    df_opstine['geometry'] = df_opstine.wkt.apply(wkt.loads)
    gdf_opstine = gpd.GeoDataFrame(df_opstine, geometry='geometry', crs="EPSG:32634")
    gdf_opstine.to_crs("EPSG:4326", inplace=True)
    gdf_opstine.sindex

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
                   'opstina_povrsina', 'okrug_sifra', 'okrug_ime', 'okrug_imel', 'wkt'], inplace=True, axis=1)

        if len(addresses_in_opstina) == 0:
            print(f"{opstina} doesn't seem to have any address")
            continue

        pd.DataFrame(addresses_in_opstina).to_csv(csv_file_path, index=False)


if __name__ == '__main__':
    main()
