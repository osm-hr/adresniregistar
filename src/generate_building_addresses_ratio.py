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


counter = 1
gdf_rgz_cache = {}


def count_addresses(data_path, opstina, naselje_geom):
    global counter
    print(f'{counter} - {opstina}')
    counter = counter + 1

    input_rgz_file = os.path.join(data_path, f'rgz/csv/{opstina}.csv')
    if not os.path.exists(input_rgz_file):
        print(f"    Missing file {input_rgz_file}, cannot process opstina {opstina}")
        return None

    global gdf_rgz_cache
    if opstina in gdf_rgz_cache:
        gdf_opstina_addresses = gdf_rgz_cache[opstina]
    else:
        df_opstina_addresses = pd.read_csv(input_rgz_file)
        df_opstina_addresses['rgz_geometry'] = df_opstina_addresses.rgz_geometry.apply(wkt.loads)
        gdf_opstina_addresses = gpd.GeoDataFrame(df_opstina_addresses, geometry='rgz_geometry', crs="EPSG:4326")
        gdf_opstina_addresses.sindex
        gdf_rgz_cache[opstina] = gdf_opstina_addresses

    naselje_gdf = gpd.GeoDataFrame([{'geometry': naselje_geom}], crs="EPSG:4326")
    naselje_gdf.sindex
    only_naselje_addresses = gdf_opstina_addresses.sjoin(naselje_gdf, how='inner', predicate='intersects')

    return len(only_naselje_addresses)


def main():
    cwd = os.getcwd()
    data_path = os.path.join(cwd, 'data')
    osm_path = os.path.join(cwd, 'data/osm')

    pbf_file = os.path.join(osm_path, 'download/serbia.osm.pbf')

    gdf_naselje = get_naselje_boundaries(cwd)

    # Calculate addresses per opstina
    gdf_naselje['addresses_count'] = gdf_naselje.apply(lambda row: count_addresses(data_path, row.opstina_imel, row.geometry), axis=1)
    gdf_naselje = gdf_naselje[pd.notna(gdf_naselje.addresses_count)]
    print(len(gdf_naselje))
    if len(gdf_naselje) != 4721:
        raise Exception("Some or all RGZ files missing! Bailing out")

    # Calculate buildings per opstina
    gdf_buildings = get_all_buildings(pbf_file)

    # For testing purposes, save and load gdf_buildings like this
    #pd.DataFrame(gdf_buildings).to_csv('/home/branko/src/adresniregistar/data/temp_gdf_buildings.csv', index=False)
    #gdf_buildings = pd.read_csv('/home/branko/src/adresniregistar/data/temp_gdf_buildings.csv')
    #gdf_buildings['osm_geometry'] = gdf_buildings.osm_geometry.apply(wkt.loads)
    #gdf_buildings = gpd.GeoDataFrame(gdf_buildings, geometry='osm_geometry', crs="EPSG:4326")
    #gdf_buildings.sindex

    print("Finding naselje for each building")
    buildings_with_naselje = gdf_buildings.sjoin(gdf_naselje, how='inner', predicate='intersects')
    buildings_with_naselje.drop(['index_right', 'naselje_maticni_broj', 'naselje_ime', 'naselje_povrsina',
                                 'opstina_maticni_broj', 'opstina_ime', 'wkt'],
                                inplace=True, axis=1)
    # For testing purposes, save and load buildings_with_naselje like this
    # pd.DataFrame(buildings_with_naselje).to_csv('/home/branko/src/adresniregistar/data/temp_buildings_with_naselje.csv', index=False)
    # buildings_with_naselje = pd.read_csv('/home/branko/src/adresniregistar/data/temp_buildings_with_naselje.csv')
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
    gdf_naselje.drop(['naselje_ime', 'naselje_povrsina', 'opstina_maticni_broj', 'opstina_ime', 'geometry', 'wkt'],
                     inplace=True, axis=1)
    pd.DataFrame(gdf_naselje).to_csv(os.path.join(data_path, 'b-hn/building_housenumber_per_naselje.csv'),
                                     index=False)


if __name__ == '__main__':
    main()
