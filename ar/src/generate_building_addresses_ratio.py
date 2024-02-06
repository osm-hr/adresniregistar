# -*- coding: utf-8 -*-

import os
import pandas as pd
import geopandas as gpd
from shapely import wkt
from common import CollectRelationWaysHandler, CollectWayNodesHandler, BuildNodesCacheHandler, CollectEntitiesHandler


def get_all_buildings(pbf_file):
    # Build building geometries
    crwh = CollectRelationWaysHandler('building')
    crwh.apply_file(pbf_file)
    print(f"Collected all ways ({len(crwh.ways)}) from building relations")

    cwnh = CollectWayNodesHandler(crwh.ways, 'building')
    cwnh.apply_file(pbf_file)
    print(f"Collected all nodes ({len(cwnh.nodes)}) from building ways")

    bnch = BuildNodesCacheHandler(set(cwnh.nodes))
    bnch.apply_file(pbf_file)
    print(f"Found coordinates for all nodes ({len(bnch.nodes_cache)}) for all buildings")

    ceh = CollectEntitiesHandler(bnch.nodes_cache, cwnh.ways_cache, 'building', collect_tags=False)
    ceh.apply_file(pbf_file)
    gdf_buildings = gpd.GeoDataFrame(ceh.entities, geometry='osm_geometry', crs="EPSG:4326")
    gdf_buildings.sindex
    print(f"Found all building geometries ({len(ceh.entities)}) from PBF")
    return gdf_buildings


def get_naselje_boundaries(cwd):
    rgz_path = os.path.join(cwd, 'data/rgz')
    print("Load naselje geometries")
    gdf_naselje = pd.read_csv(os.path.join(rgz_path, 'naselje.csv'), dtype='unicode')
    gdf_naselje['geometry'] = gdf_naselje.wkt.apply(wkt.loads)
    gdf_naselje = gpd.GeoDataFrame(gdf_naselje, geometry='geometry', crs="EPSG:32634")
    gdf_naselje.to_crs("EPSG:4326", inplace=True)
    gdf_naselje.sindex
    return gdf_naselje


def main():
    cwd = os.getcwd()
    data_path = os.path.join(cwd, 'data')
    osm_path = os.path.join(cwd, 'data/osm')
    rgz_csv_path = os.path.join(cwd, 'data/rgz/csv')

    pbf_file = os.path.join(osm_path, 'download/serbia.osm.pbf')

    building_housenumber_filepath = os.path.join(data_path, 'b-hn/building_housenumber_per_naselje.csv')

    if os.path.exists(building_housenumber_filepath):
        print("File data/b-hn/building_housenumber_per_naselje.csv already exists")
        return

    gdf_naselje = get_naselje_boundaries(cwd)

    # Calculate addresses per naselje
    # First union all addresses in RGZ for whole of Serbia in variable `gdf_rgz_addresses`,
    # then do spatial join and count them per naselje
    total_csvs = len(os.listdir(rgz_csv_path))
    if total_csvs < 168:
        raise Exception("Some or all RGZ files missing! Bailing out")

    print("Getting all RGZ addresses")
    df_rgz_per_opstina = []
    for i, file in enumerate(sorted(os.listdir(rgz_csv_path))):
        if not file.endswith(".csv"):
            continue
        input_rgz_file = os.path.join(rgz_csv_path, f'{file[:-4]}.csv')
        df_rgz = pd.read_csv(input_rgz_file, dtype={'rgz_kucni_broj_id': str})
        df_rgz.drop(['rgz_opstina_mb', 'rgz_opstina'], inplace=True, axis=1)
        df_rgz_per_opstina.append(df_rgz)
    df_rgz = pd.concat(df_rgz_per_opstina)
    df_rgz['rgz_geometry'] = df_rgz.rgz_geometry.apply(wkt.loads)
    gdf_rgz_addresses = gpd.GeoDataFrame(df_rgz, geometry='rgz_geometry', crs="EPSG:4326")
    gdf_rgz_addresses.sindex

    # For testing purposes, save and load addresses like this
    # pd.DataFrame(gdf_rgz).to_csv('~/src/adresniregistar/ar/data/temp_gdf_rgz_addresses.csv', index=False)
    # gdf_rgz_addresses = pd.read_csv('~/src/adresniregistar/ar/data/temp_gdf_rgz_addresses.csv')
    # gdf_rgz_addresses['rgz_geometry'] = gdf_rgz_addresses.rgz_geometry.apply(wkt.loads)
    # gdf_rgz_addresses = gpd.GeoDataFrame(gdf_rgz_addresses, geometry='rgz_geometry', crs="EPSG:4326")
    # gdf_rgz_addresses.sindex

    print("Calculating address count per naselje")
    rgz_addresses_with_naselje = gdf_rgz_addresses.sjoin(gdf_naselje, how='inner', predicate='intersects')
    rgz_addresses_count_per_naselje = rgz_addresses_with_naselje.groupby(['naselje_imel', 'opstina_imel'])['naselje_imel', 'opstina_imel'].count()
    gdf_naselje = gdf_naselje.join(rgz_addresses_count_per_naselje, how='left', on=['naselje_imel', 'opstina_imel'], rsuffix='_addresses_count')
    gdf_naselje.rename(columns={'naselje_imel_addresses_count': 'addresses_count'}, inplace=True)
    gdf_naselje.drop(['opstina_imel_addresses_count'], inplace=True, axis=1)
    gdf_naselje.fillna(value={'addresses_count': 0}, inplace=True, )
    gdf_naselje['addresses_count'] = gdf_naselje['addresses_count'].astype(int)

    # Calculate buildings per opstina
    # Get all OSM buildings from PBF, then do spatial join and count them per naselje
    print("Getting all OSM buildings")
    gdf_buildings = get_all_buildings(pbf_file)

    # For testing purposes, save and load gdf_buildings like this
    #pd.DataFrame(gdf_buildings).to_csv('~/src/adresniregistar/ar/data/temp_gdf_buildings.csv', index=False)
    #gdf_buildings = pd.read_csv('~/src/adresniregistar/ar/data/temp_gdf_buildings.csv')
    #gdf_buildings['osm_geometry'] = gdf_buildings.osm_geometry.apply(wkt.loads)
    #gdf_buildings = gpd.GeoDataFrame(gdf_buildings, geometry='osm_geometry', crs="EPSG:4326")
    #gdf_buildings.sindex

    print("Calculating building count per naselje")
    buildings_with_naselje = gdf_buildings.sjoin(gdf_naselje, how='inner', predicate='intersects')
    buildings_with_naselje.drop(['index_right', 'naselje_maticni_broj', 'naselje_ime', 'naselje_povrsina',
                                 'opstina_maticni_broj', 'opstina_ime', 'wkt'],
                                inplace=True, axis=1)

    # For testing purposes, save and load buildings_with_naselje like this
    # pd.DataFrame(buildings_with_naselje).to_csv('~/adresniregistar/ar/data/temp_buildings_with_naselje.csv', index=False)
    # buildings_with_naselje = pd.read_csv('~/src/adresniregistar/ar/data/temp_buildings_with_naselje.csv')
    # buildings_with_naselje['osm_geometry'] = buildings_with_naselje.osm_geometry.apply(wkt.loads)
    # buildings_with_naselje = gpd.GeoDataFrame(buildings_with_naselje, geometry='osm_geometry', crs="EPSG:4326")
    # buildings_with_naselje.sindex

    building_count_per_naselje = buildings_with_naselje.groupby(['naselje_imel', 'opstina_imel'])['naselje_imel', 'opstina_imel'].count()
    gdf_naselje = gdf_naselje.join(building_count_per_naselje, how='left', on=['naselje_imel', 'opstina_imel'], rsuffix='_building_count')
    gdf_naselje.rename(columns={'naselje_imel_building_count': 'building_count'}, inplace=True)
    gdf_naselje.drop(['opstina_imel_building_count'], inplace=True, axis=1)
    gdf_naselje.fillna(value={'building_count': 0}, inplace=True, )
    gdf_naselje['building_count'] = gdf_naselje['building_count'].astype(int)

    # Prepare for export
    print("Exporting building / housenumber ratio to CSV")
    gdf_naselje.drop(['naselje_ime', 'naselje_povrsina', 'opstina_maticni_broj', 'opstina_ime', 'geometry', 'wkt'],
                     inplace=True, axis=1)
    pd.DataFrame(gdf_naselje).to_csv(building_housenumber_filepath, index=False)


if __name__ == '__main__':
    main()
