# -*- coding: utf-8 -*-

import os
import datetime

import geopandas as gpd
import pandas as pd
from shapely import wkt

from common import CollectRelationWaysHandler, CollectWayNodesHandler, BuildNodesCacheHandler, CollectEntitiesHandler


def load_removed_addresses_from_osm(cwd):
    collect_path = os.path.join(cwd, 'data/osm')
    pbf_file = os.path.join(collect_path, 'download/serbia.osm.pbf')

    crwh = CollectRelationWaysHandler('removed:ref:RS:kucni_broj')
    crwh.apply_file(pbf_file)
    print(f"Collected all ways ({len(crwh.ways)}) from relations")

    cwnh = CollectWayNodesHandler(crwh.ways, 'removed:ref:RS:kucni_broj')
    cwnh.apply_file(pbf_file)
    print(f"Collected all nodes ({len(cwnh.nodes)}) from ways")

    bnch = BuildNodesCacheHandler(set(cwnh.nodes))
    bnch.apply_file(pbf_file)
    print(f"Found coordinates for all nodes ({len(bnch.nodes_cache)})")

    ceh = CollectEntitiesHandler(bnch.nodes_cache, cwnh.ways_cache, 'removed:ref:RS:kucni_broj', collect_tags=True)
    ceh.apply_file(pbf_file)
    print(f"Collected all addresses ({len(ceh.entities)})")

    gdf_removed_addresses = gpd.GeoDataFrame(ceh.entities, geometry='osm_geometry', crs="EPSG:4326")
    gdf_removed_addresses['removed:ref:RS:kucni_broj'] = gdf_removed_addresses.apply(lambda row: row.tags['removed:ref:RS:kucni_broj'], axis=1)
    gdf_removed_addresses.drop(['osm_country', 'osm_city', 'osm_postcode', 'tags'], inplace=True, axis=1)
    gdf_removed_addresses.sindex
    print(f"Found all removed geometries ({len(ceh.entities)}) from PBF")

    # For testing purposes, save and load gdf_buildings like this
    # pd.DataFrame(gdf_removed_addresses).to_csv('~/src/adresniregistar/ar/data/gdf_removed_addresses.csv', index=False)
    # gdf_removed_addresses = pd.read_csv('~/src/adresniregistar/ar/data/gdf_removed_addresses.csv')
    # gdf_removed_addresses['osm_geometry'] = gdf_removed_addresses.osm_geometry.apply(wkt.loads)
    # gdf_removed_addresses = gpd.GeoDataFrame(gdf_removed_addresses, geometry='osm_geometry', crs="EPSG:4326")
    # gdf_removed_addresses.sindex
    return gdf_removed_addresses


def load_opstine(cwd):
    rgz_path = os.path.join(cwd, 'data/rgz')

    if not os.path.exists(os.path.join(rgz_path, 'opstina.csv')):
        print("Skinite opstine.zip sa https://opendata.geosrbija.rs i otpakujte opstina.csv u data/rgz/ direktorijum")
        raise Exception()

    print("Load opstine geometries")
    df_opstine = pd.read_csv(os.path.join(rgz_path, 'opstina.csv'), dtype='unicode')
    df_opstine['geometry'] = df_opstine.wkt.apply(wkt.loads)
    gdf_opstine = gpd.GeoDataFrame(df_opstine, geometry='geometry', crs="EPSG:32634")
    gdf_opstine.to_crs("EPSG:4326", inplace=True)
    gdf_opstine.sindex

    return gdf_opstine


def extract_removal_date(osm_id, note):
    if 'Izbrisano iz RGZ-a' not in note:
        print(f'Note for {osm_id} do not contain "Izbrisano iz RGZ-a" text')
        return ''

    if ';' in note:
        notes = note.split(';')
        for n in notes:
            if 'Izbrisano iz RGZ-a' in n:
                note = n
                break
    extracted_date = note[len('Izbrisano iz RGZ-a '):]
    try:
        _ = datetime.datetime.strptime('2023-07-15', '%Y-%m-%d')
        return extracted_date
    except ValueError:
        print(f'Note for {osm_id} cannot be parsed for date')
    return ''


def main():
    cwd = os.getcwd()
    qa_path = os.path.join(cwd, 'data/qa')

    if os.path.exists(os.path.join(qa_path, 'removed_addresses.csv')):
        return

    gdf_removed_addresses = load_removed_addresses_from_osm(cwd)
    gdf_opstine = load_opstine(cwd)

    print("Finding opstina for each removed address")
    gdf_removed_addresses_with_opstina = gdf_removed_addresses.sjoin(gdf_opstine, how='inner', predicate='intersects')
    gdf_removed_addresses_with_opstina['removal_date'] = gdf_removed_addresses_with_opstina.apply(
        lambda row: extract_removal_date(row.osm_id, row.note), axis=1)
    gdf_removed_addresses_with_opstina.drop(['index_right', 'opstina_maticni_broj', 'opstina_ime', 'opstina_povrsina',
                                             'okrug_sifra', 'okrug_ime', 'okrug_imel', 'wkt'], inplace=True, axis=1)

    pd.DataFrame(gdf_removed_addresses_with_opstina).to_csv(os.path.join(qa_path, 'removed_addresses.csv'), index=False)
    print("Created removed_addresses.csv")


if __name__ == '__main__':
    main()
