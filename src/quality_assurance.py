# -*- coding: utf-8 -*-

import json
import os

import geopandas as gpd
import osmium
import pandas as pd
from shapely import wkt

from common import CollectRelationWaysHandler, CollectWayNodesHandler, BuildNodesCacheHandler, CollectEntitiesHandler


class CollectRefAddressesHandler(osmium.SimpleHandler):
    """
    Iterates for all addresses with ref:RS:kucni_broj and collect them
    """
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.addresses = {}

    def node(self, n):
        if n.tags.get('ref:RS:kucni_broj'):
            ref = n.tags.get('ref:RS:kucni_broj')
            if ref not in self.addresses:
                self.addresses[ref] = []
            self.addresses[ref].append({
                'id': n.id,
                'type': 'node',
                'tags': {t.k: t.v for t in n.tags}
            })

    def way(self, w):
        if w.tags.get('ref:RS:kucni_broj'):
            ref = w.tags.get('ref:RS:kucni_broj')
            if ref not in self.addresses:
                self.addresses[ref] = []
            self.addresses[ref].append({
                'id': w.id,
                'type': 'way',
                'tags': {t.k: t.v for t in w.tags}
            })

    def relation(self, r):
        if r.tags.get('ref:RS:kucni_broj'):
            ref = r.tags.get('ref:RS:kucni_broj')
            if ref not in self.addresses:
                self.addresses[ref] = []
            self.addresses[ref].append({
                'id': r.id,
                'type': 'relation',
                'tags': {t.k: t.v for t in r.tags}
            })


def find_addresses_in_buildings(cwd):
    osm_path = os.path.join(cwd, 'data/osm')
    rgz_path = os.path.join(cwd, 'data/rgz')
    qa_path = os.path.join(cwd, 'data/qa')
    pbf_file = os.path.join(osm_path, 'download/serbia.osm.pbf')

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

    ceh = CollectEntitiesHandler(bnch.nodes_cache, cwnh.ways_cache, 'building')
    ceh.apply_file(pbf_file)
    gdf_buildings = gpd.GeoDataFrame(ceh.entities, geometry='osm_geometry', crs="EPSG:4326")
    gdf_buildings.sindex
    print(f"Found all building geometries ({len(ceh.entities)}) from PBF")

    # For testing purposes, save and load gdf_buildings like this
    # pd.DataFrame(gdf_buildings).to_csv('/home/branko/src/adresniregistar/data/gdf_buildings.csv', index=False)
    # gdf_buildings = pd.read_csv('/home/branko/src/adresniregistar/data/gdf_buildings.csv')
    # gdf_buildings['osm_geometry'] = gdf_buildings.osm_geometry.apply(wkt.loads)
    # gdf_buildings = gpd.GeoDataFrame(gdf_buildings, geometry='osm_geometry', crs="EPSG:4326")
    # gdf_buildings.sindex

    # # Build node geometries
    ceh = CollectEntitiesHandler(nodes_cache=set(), ways_cache=set(), tag_to_search='addr:housenumber', collect_only_nodes=True)
    ceh.apply_file(pbf_file)
    gdf_addresses = gpd.GeoDataFrame(ceh.entities, geometry='osm_geometry', crs="EPSG:4326")
    gdf_addresses.sindex
    print(f"Found all address nodes ({len(ceh.entities)}) from PBF")

    df_opstine = pd.read_csv(os.path.join(rgz_path, 'opstina.csv'))
    df_opstine['geometry'] = df_opstine.wkt.apply(wkt.loads)
    gdf_opstine = gpd.GeoDataFrame(df_opstine, geometry='geometry', crs="EPSG:32634")
    gdf_opstine.to_crs("EPSG:4326", inplace=True)
    gdf_opstine.sindex
    print(f"Loaded all opstine geometries ({len(gdf_opstine)})")

    addresses_per_opstina = gdf_addresses.sjoin(gdf_opstine, how='inner', predicate='intersects')
    addresses_per_opstina.sindex
    addresses_per_opstina.drop(['osm_country', 'osm_city', 'osm_postcode', 'index_right', 'opstina_maticni_broj',
                                'opstina_ime', 'opstina_povrsina', 'okrug_sifra', 'okrug_ime', 'okrug_imel', 'wkt'],
                               inplace=True, axis=1)
    print("Split all addresses per opstina")

    # For testing purposes, save and load addresses_per_opstina like this
    # pd.DataFrame(addresses_per_opstina).to_csv('/home/branko/src/adresniregistar/data/addresses_per_opstina.csv', index=False)
    # addresses_per_opstina = pd.read_csv('/home/branko/src/adresniregistar/data/addresses_per_opstina.csv')
    # addresses_per_opstina['osm_geometry'] = addresses_per_opstina.osm_geometry.apply(wkt.loads)
    # addresses_per_opstina = gpd.GeoDataFrame(addresses_per_opstina, geometry='osm_geometry', crs="EPSG:4326")
    # addresses_per_opstina.sindex

    addresses_in_buildings_per_opstina = addresses_per_opstina.sjoin(gdf_buildings, how='inner', predicate='within')
    addresses_in_buildings_per_opstina.drop(['osm_country', 'osm_city', 'osm_postcode'], inplace=True, axis=1)
    pd.DataFrame(addresses_in_buildings_per_opstina).to_csv(os.path.join(qa_path, 'addresses_in_buildings_per_opstina.csv'), index=False)


def find_duplicated_refs(cwd):
    # Finds addresses which have same ref:RS:kucni_broj reference
    osm_path = os.path.join(cwd, 'data/osm')
    pbf_file = os.path.join(osm_path, 'download/serbia.osm.pbf')
    qa_path = os.path.join(cwd, 'data/qa')
    json_file_path = os.path.join(qa_path, 'duplicated_refs.json')

    crah = CollectRefAddressesHandler()
    crah.apply_file(pbf_file)
    print(f"Found all addresses with refs ({len(crah.addresses)} from PBF")

    if os.path.exists(json_file_path):
        print("File data/qa/duplicated_refs.json already exists")
        return

    output_dict = []
    for k, v in crah.addresses.items():
        if len(v) > 1:
            output_dict.append({
                'ref:RS:kucni_broj': k,
                'duplicates': v
            })

    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(output_dict, json_file, ensure_ascii=False)


def main():
    cwd = os.getcwd()
    find_addresses_in_buildings(cwd)
    find_duplicated_refs(cwd)


if __name__ == '__main__':
    main()
