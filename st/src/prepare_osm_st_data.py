# -*- coding: utf-8 -*-

import os

import geopandas as gpd
import pandas as pd
from shapely import wkt

from common import OPSTINE_TO_SKIP


def main():
    cwd = os.getcwd()
    osm_path = os.path.join(cwd, 'data/osm')
    rgz_path = os.path.join(cwd, '../ar/data/rgz')

    if not os.path.exists(os.path.join(rgz_path, 'opstina.csv')):
        print("Skinite opstine.zip sa https://opendata.geosrbija.rs i otpakujte opstina.csv u data/rgz/ direktorijum")
        return

    print("Load opstine geometries")
    df_opstine = pd.read_csv(os.path.join(rgz_path, 'opstina.csv'), dtype='unicode')
    df_opstine['geometry'] = df_opstine.wkt.apply(wkt.loads)
    gdf_opstine = gpd.GeoDataFrame(df_opstine, geometry='geometry', crs="EPSG:32634")
    gdf_opstine.to_crs("EPSG:4326", inplace=True)
    gdf_opstine.sindex

    print("Load all OSM addresses")
    df_streets = pd.read_csv(os.path.join(osm_path, 'streets.csv'), dtype={'ref:RS:ulica': object})
    df_streets['osm_geometry'] = df_streets.osm_geometry.apply(wkt.loads)
    gdf_streets = gpd.GeoDataFrame(df_streets, geometry='osm_geometry', crs="EPSG:4326")
    gdf_streets.sindex

    print("Finding opstina for each OSM street")
    streets_with_opstina = gdf_streets.sjoin(gdf_opstine, how='inner', predicate='intersects')
    streets_with_opstina['ref:RS:ulica'] = streets_with_opstina['ref:RS:ulica'].astype('str')

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
        streets_in_opstina = streets_with_opstina[streets_with_opstina['opstina_imel'] == opstina].copy()
        streets_in_opstina.drop(['index_right', 'opstina_maticni_broj', 'opstina_ime', 'opstina_imel',
                   'opstina_povrsina', 'okrug_sifra', 'okrug_ime', 'okrug_imel', 'wkt'], inplace=True, axis=1)

        if len(streets_in_opstina) == 0:
            print(f"{opstina} doesn't seem to have any address")
            continue

        pd.DataFrame(streets_in_opstina).to_csv(csv_file_path, index=False)


if __name__ == '__main__':
    main()
