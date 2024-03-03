# -*- coding: utf-8 -*-

import argparse
import os
import time
from itertools import chain

import osmapi
import pandas as pd
from jinja2 import Environment, FileSystemLoader

from common import xml_escape, cyr2lat_small, cyr2intname, OsmEntitiesCacheHandler, CollectWayNodesHandler
from street_mapping import StreetMapping


def do_opstina(data_path, osm_entities_cache, street_mappings: StreetMapping, opstina):
    print(f"Doing opstina {opstina}")

    osm_ways = []

    analysis_path = os.path.join(data_path, 'analysis')
    opstina_csv_filepath = os.path.join(analysis_path,  f'{opstina.upper()}.csv')
    if not os.path.exists(opstina_csv_filepath):
        raise Exception(f"Missing file {os.path.relpath(opstina_csv_filepath)}")

    df_opstina = pd.read_csv(opstina_csv_filepath, dtype={'conflated_osm_way_length': object})
    df_opstina['rgz_ulica_mb'] = df_opstina['rgz_ulica_mb'].astype('str')
    df_opstina = df_opstina[~df_opstina.is_zaseok]
    only_matched_addresses = df_opstina[pd.notna(df_opstina.found_osm_id)]
    print(f"Iterating over {len(only_matched_addresses)} entries")

    for _, address in only_matched_addresses.iterrows():
        for found_way_id, found_intersection, found_osm_way_length in zip(address.found_osm_id.split(','), address.found_intersection.split(','),  address.found_osm_way_length.split(',')):
            if found_way_id[0] == 'n':
                #print(f"Encountered node {found_way_id}, skipping")
                continue
            if found_way_id[0] == 'r':
                #print(f"Encountered relation {found_way_id}, skipping")
                continue

            if float(found_intersection) < 0.9:
                #print(f"Skipping intersection of {found_intersection}")
                continue
            if float(found_osm_way_length) < 20:
                #print(f"Skipping length of {found_osm_way_length}m")
                continue

            way_id = int(found_way_id[1:])
            entity = osm_entities_cache.ways_cache[way_id]

            if 'bridge' in entity['tags']:
                #print("Skipping bridge")
                continue

            if 'name' in entity['tags']:
                #print("Skipping highways with name tag")
                continue
            if 'name:sr' in entity['tags']:
                print("Skipping highways with name:sr tag")
                continue
            if 'name:sr-Latn' in entity['tags']:
                print("Skipping highways with name:sr-Latn tag")
                continue
            if 'ref:RS:ulica' in entity['tags']:
                print("Skipping highways that already have ref:RS:ulica")
                continue

            new_tags = dict(entity['tags'], **{
                'ref:RS:ulica': str(address.rgz_ulica_mb),
                'name': address.rgz_ulica_proper,
                'name:sr': address.rgz_ulica_proper,
                'name:sr-Latn': cyr2lat_small(address.rgz_ulica_proper),
                'int_name': cyr2intname(address.rgz_ulica_proper)
            })
            osm_ways.append({
                'id': way_id,
                'tags': {k: xml_escape(v) for k, v in new_tags.items()},
                'nodes': entity['nodes'],
                'version': entity['version']
            })

    print(f"Found {len(osm_ways)} ways")
    return osm_ways


def do_all_opstina(data_path, osm_entities_cache, street_mappings, df_opstine):
    osm_csv_path = os.path.join(data_path, 'osm/csv')
    osm_ways_all = {}
    for i, file in enumerate(sorted(os.listdir(osm_csv_path))):
        if not file.endswith(".csv"):
            continue
        okrug = df_opstine[df_opstine.opstina_imel == file[:-4]].okrug_imel.iloc[0]
        if okrug not in osm_ways_all:
            osm_ways_all[okrug] = []
        osm_ways_in_opstina = do_opstina(data_path, osm_entities_cache, street_mappings, file[:-4])
        osm_ways_all[okrug] += osm_ways_in_opstina
    return osm_ways_all


def build_osm_entities_cache(data_path):
    analysis_path = os.path.join(data_path, 'analysis')

    pbf_file = os.path.join(data_path, 'osm/download/serbia.osm.pbf')
    nodes_to_cache, ways_to_cache = [], []

    # Collects nodes and ways from analysis
    for i, file in enumerate(sorted(os.listdir(analysis_path))):
        if not file.endswith(".csv"):
            continue
        df_opstina = pd.read_csv(os.path.join(analysis_path, file))
        osm_entites_to_cache = df_opstina[pd.notna(df_opstina.found_osm_id)]['found_osm_id']
        if len(osm_entites_to_cache) > 0:
            ways_to_cache_string = list(chain(*[w.split(',') for w in osm_entites_to_cache]))
            ways_to_cache += [int(w[1:]) for w in ways_to_cache_string if w[0] == 'w']

    print("Using PBF to build cache")

    osm_entities_cache = OsmEntitiesCacheHandler(set(), set(ways_to_cache))

    osm_entities_cache.apply_file(pbf_file)
    return osm_entities_cache


def main():
    cwd = os.getcwd()
    data_path = os.path.join(cwd, 'data')

    parser = argparse.ArgumentParser(
        description='generate_maproulette.py - Generates .osm for changes that can be done in Map Roulette')
    parser.add_argument('--opstina', default='', required=False, help='Opstina to process')
    args = parser.parse_args()

    print("Building cache of OSM entities")
    osm_entities_cache = build_osm_entities_cache(data_path)

    print("Loading normalized street names mapping")
    street_mappings = StreetMapping(os.path.join(cwd, '..', 'ar'))

    df_opstine = pd.read_csv(os.path.join(os.path.join(cwd, '..', 'ar/data/rgz'), 'opstina.csv'), dtype='unicode')

    osm_ways = {}
    if args.opstina != '':
        okrug = df_opstine[df_opstine.opstina_imel==args.opstina].okrug_imel.iloc[0]
        osm_ways_opstina = do_opstina(data_path, osm_entities_cache, street_mappings, args.opstina)
        osm_ways = {okrug: osm_ways_opstina}
    else:
        osm_ways = do_all_opstina(data_path, osm_entities_cache, street_mappings, df_opstine)

    split_amount = 1
    env = Environment(loader=FileSystemLoader(searchpath='./templates'))
    template = env.get_template('matched_streets.osm')

    for okrug in osm_ways.keys():
        for i in range(split_amount):
            osm_ways_in_opstina = osm_ways[okrug]
            ways_to_render = []
            for way in osm_ways_in_opstina:
                if way['id'] % split_amount == i:
                    ways_to_render.append(way)
            output = template.render(osm_ways=ways_to_render, min_lat=None, min_lon=None, max_lat=None, max_lon=None)
            with open(f'maproulette-{okrug}.osm', 'w', encoding='utf-8') as fh:
                fh.write(output)


if __name__ == '__main__':
    main()
