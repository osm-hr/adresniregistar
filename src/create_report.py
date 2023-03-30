# -*- coding: utf-8 -*-

import csv
import datetime
import json
import os

import osmium
import pandas as pd
from jinja2 import Environment, FileSystemLoader

from common import cyr2lat, normalize_name, normalize_name_latin, xml_escape
from common import AddressInBuildingResolution

street_mappings = {}


class CollectWayNodesHandler(osmium.SimpleHandler):
    """
    Iterates for all given ways and collects their nodes
    """
    def __init__(self, ways):
        osmium.SimpleHandler.__init__(self)
        self.ways = ways
        self.nodes = []

    def way(self, w):
        if w.id in self.ways:
            self.nodes += [n.ref for n in w.nodes]


class OsmEntitiesCacheHandler(osmium.SimpleHandler):
    def __init__(self, nodes, ways):
        osmium.SimpleHandler.__init__(self)
        self.nodes = nodes
        self.ways = ways
        self.nodes_cache = {}
        self.ways_cache = {}

    def node(self, n):
        if n.id in self.nodes:
            self.nodes_cache[n.id] = {
                'lat': n.location.lat,
                'lon': n.location.lon,
                'tags': {t.k: t.v for t in n.tags},
                'version': n.version
            }

    def way(self, w):
        if w.id in self.ways:
            self.ways_cache[w.id] = {
                'tags': {t.k: t.v for t in w.tags},
                'nodes': [n.ref for n in w.nodes],
                'version': w.version
            }


def build_osm_entities_cache(data_path):
    analysis_path = os.path.join(data_path, 'analysis')
    qa_path = os.path.join(data_path, 'qa')

    pbf_file = os.path.join(data_path, 'osm/download/serbia.osm.pbf')
    nodes_to_cache, ways_to_cache = [], []

    # Collects nodes and ways from analysis
    for i, file in enumerate(sorted(os.listdir(analysis_path))):
        if not file.endswith(".csv"):
            continue
        df_opstina = pd.read_csv(os.path.join(analysis_path, file), dtype={'conflated_osm_housenumber': object, 'osm_housenumber': object})
        osm_entites_to_cache = df_opstina[pd.notna(df_opstina.osm_id) & (df_opstina.matching)]['osm_id']
        nodes_to_cache += [int(n[1:]) for n in list(osm_entites_to_cache[osm_entites_to_cache.str.startswith('n')])]
        ways_to_cache += [int(w[1:]) for w in list(osm_entites_to_cache[osm_entites_to_cache.str.startswith('w')])]

    # Collects nodes and ways from qa/addresses_in_buildings_per_opstina.csv
    df_addresses_in_buildings_per_opstina = pd.read_csv(os.path.join(qa_path, 'addresses_in_buildings_per_opstina.csv'))
    df_addresses_in_buildings_per_opstina = df_addresses_in_buildings_per_opstina[df_addresses_in_buildings_per_opstina.resolution == AddressInBuildingResolution.MERGE_ADDRESS_TO_BUILDING.value]
    nodes_to_cache += [int(n[1:]) for n in list(df_addresses_in_buildings_per_opstina['osm_id_left']) if n[0] == 'n']
    ways_to_cache += [int(w[1:]) for w in list(df_addresses_in_buildings_per_opstina['osm_id_right']) if w[0] == 'w']

    cwnh = CollectWayNodesHandler(set(ways_to_cache))
    cwnh.apply_file(pbf_file)

    osm_entities_cache = OsmEntitiesCacheHandler(set(nodes_to_cache).union(cwnh.nodes), set(ways_to_cache))
    osm_entities_cache.apply_file(pbf_file)
    return osm_entities_cache


def load_mappings(data_path):
    global street_mappings
    with open(os.path.join(data_path, 'mapping', 'mapping.csv'), encoding='utf-8') as mapping_csv_file:
        reader = csv.DictReader(mapping_csv_file)
        for row in reader:
            street_mappings[row['rgz_name']] = row['name']


def generate_osm_files_matched_addresses(env, osm_entities_cache, opstina_dir_path, opstina_name, naselje, df_naselje):
    naselje_dir_path = os.path.join(opstina_dir_path, opstina_name)
    split_limit = 100

    template = env.get_template('matched_address.osm')
    osm_files = []
    osm_nodes, osm_ways = [], []
    old_counter = 0
    counter = 0
    only_matched_addresses = df_naselje[pd.isna(df_naselje.conflated_osm_id) & pd.notna(df_naselje.osm_id) & df_naselje.matching]
    for _, address in only_matched_addresses.sort_values(['rgz_ulica', 'rgz_kucni_broj']).iterrows():
        if address.osm_id[0] == 'r':
            print(f"Encountered relation {address.osm_id}, had to be merged manually... ", end='')
            continue

        if counter > 0 and counter % split_limit == 0:
            output = template.render(osm_nodes=osm_nodes, osm_ways=osm_ways)
            filename = f'{normalize_name(naselje["name_lat"])}-matched-{counter}.osm'
            osm_file_path = os.path.join(naselje_dir_path, filename)
            with open(osm_file_path, 'w', encoding='utf-8') as fh:
                fh.write(output)
            osm_files.append(
                {
                    'name': f'{old_counter+1}-{counter}',
                    'url': f'https://openstreetmap.rs/download/ar/opstine/{opstina_name}/{filename}'
                }
            )
            old_counter = counter
            osm_nodes, osm_ways = [], []

        if address.osm_id[0] == 'n':
            counter = counter + 1
            node_id = int(address.osm_id[1:])
            entity = osm_entities_cache.nodes_cache[node_id]
            already_exists = any(n for n in osm_nodes if n['id'] == node_id)
            if not already_exists:
                new_tags = dict(entity['tags'], **{'ref:RS:kucni_broj': str(address.rgz_kucni_broj_id)})
                osm_nodes.append({
                    'id': node_id,
                    'lat': entity['lat'],
                    'lon': entity['lon'],
                    'tags': {k: xml_escape(v) for k, v in new_tags.items()},
                    'version': entity['version']
                })
        elif address.osm_id[0] == 'w':
            counter = counter + 1
            entity = osm_entities_cache.ways_cache[int(address.osm_id[1:])]
            new_tags = dict(entity['tags'], **{'ref:RS:kucni_broj': str(address.rgz_kucni_broj_id)})
            osm_ways.append({
                'id': int(address.osm_id[1:]),
                'tags': {k: xml_escape(v) for k, v in new_tags.items()},
                'nodes': entity['nodes'],
                'version': entity['version']
            })
            for node in entity['nodes']:
                node_entity = osm_entities_cache.nodes_cache[node]
                already_exists = any(n for n in osm_nodes if n['id'] == node)
                if not already_exists:
                    osm_nodes.append({
                        'id': node,
                        'lat': node_entity['lat'],
                        'lon': node_entity['lon'],
                        'tags': {k: xml_escape(v) for k, v in node_entity['tags'].items()},
                        'version': node_entity['version']
                    })

    # Final write
    if len(osm_nodes) > 0 or len(osm_ways) > 0:
        output = template.render(osm_nodes=osm_nodes, osm_ways=osm_ways)
        filename = f'{normalize_name(naselje["name_lat"])}-matched-{counter}.osm'
        osm_file_path = os.path.join(naselje_dir_path, filename)
        with open(osm_file_path, 'w', encoding='utf-8') as fh:
            fh.write(output)
        osm_files.append(
            {
                'name': f'{old_counter + 1}-{counter}',
                'url': f'https://openstreetmap.rs/download/ar/opstine/{opstina_name}/{filename}'
            }
        )

    return osm_files


def generate_osm_files_new_addresses(env, opstina_dir_path, opstina_name, naselje, df_naselje):
    global street_mappings
    naselje_dir_path = os.path.join(opstina_dir_path, opstina_name)

    template = env.get_template('new_address.osm')
    osm_files = []
    osm_entities = []
    counter = 0
    only_not_found_addresses = df_naselje[pd.isna(df_naselje.conflated_osm_id) & pd.isna(df_naselje.osm_id)]
    for _, address in only_not_found_addresses.sort_values(['rgz_ulica', 'rgz_kucni_broj']).iterrows():
        location = address['rgz_geometry'][7:-1].split(' ')
        location_lon = round(float(location[0]), 6)
        location_lat = round(float(location[1]), 6)

        if len(osm_entities) == 100:
            old_counter = counter
            counter = counter + len(osm_entities)
            output = template.render(osm_entities=osm_entities)
            filename = f'{normalize_name(naselje["name_lat"])}-new-{counter}.osm'
            osm_file_path = os.path.join(naselje_dir_path, filename)
            with open(osm_file_path, 'w', encoding='utf-8') as fh:
                fh.write(output)
            osm_files.append(
                {
                    'name': f'{old_counter+1}-{counter}',
                    'url': f'https://openstreetmap.rs/download/ar/opstine/{opstina_name}/{filename}'
                }
            )
            osm_entities = []

        osm_entities.append({
            'id': 0 - (len(osm_entities) + 1),
            'lat': location_lat,
            'lon': location_lon,
            'street': street_mappings[address['rgz_ulica']],
            'housenumber': normalize_name_latin(address['rgz_kucni_broj']),
            'ulica': address['rgz_ulica_mb'],
            'kucni_broj': address['rgz_kucni_broj_id']
        })

    # Final write
    if len(osm_entities) > 0:
        old_counter = counter
        counter = counter + len(osm_entities)
        output = template.render(osm_entities=osm_entities)
        filename = f'{normalize_name(naselje["name_lat"])}-new-{counter}.osm'
        osm_file_path = os.path.join(naselje_dir_path, filename)
        with open(osm_file_path, 'w', encoding='utf-8') as fh:
            fh.write(output)
        osm_files.append(
            {
                'name': f'{old_counter + 1}-{counter}',
                'url': f'https://openstreetmap.rs/download/ar/opstine/{opstina_name}/{filename}'
            }
        )

    return osm_files


def generate_naselje(env, osm_entities_cache, opstina_dir_path, opstina_name, naselje, df_naselje):
    template = env.get_template('naselje.html')
    current_date = datetime.date.today().strftime('%Y-%m-%d')
    current_date_srb = datetime.date.today().strftime('%d.%m.%Y')
    opstina_name_norm = normalize_name(opstina_name)
    naselje_dir_path = os.path.join(opstina_dir_path, opstina_name_norm)
    if not os.path.exists(naselje_dir_path):
        os.mkdir(naselje_dir_path)

    osm_files_new_addresses = generate_osm_files_new_addresses(env, opstina_dir_path, opstina_name_norm, naselje, df_naselje)
    osm_files_matched_addresses = generate_osm_files_matched_addresses(env, osm_entities_cache, opstina_dir_path, opstina_name_norm, naselje, df_naselje)

    naselje_path = os.path.join(naselje_dir_path, f'{naselje["name_lat"]}.html')

    addresses = []
    for _, address in df_naselje.iterrows():
        location = address['rgz_geometry'][7:-1].split(' ')
        location_lon = round(float(location[0]), 6)
        location_lat = round(float(location[1]), 6)
        location_url = f'https://www.openstreetmap.org/?mlat={location_lat}&mlon={location_lon}#map=19/{location_lat}/{location_lon}'
        location_text = f'{location_lat}, {location_lon}'

        conflated_osm_link, conflated_osm_street, conflated_osm_housenumber, score, distance = '', '', '', '', ''
        is_conflated = type(address['conflated_osm_id']) == str
        if is_conflated:
            osm_type = 'node' if address['conflated_osm_id'][0] == 'n' else 'way' if address['conflated_osm_id'][0] == 'w' else 'relation'
            conflated_osm_link = f'https://www.openstreetmap.org/{osm_type}/{address["conflated_osm_id"][1:]}'
            conflated_osm_street = address['conflated_osm_street']
            conflated_osm_housenumber = address['conflated_osm_housenumber']
            score = 1
            distance = float(address['conflated_distance'])

        osm_link, osm_street, osm_housenumber = '', '', ''
        is_matched = type(address['osm_id']) == str
        if not is_conflated and is_matched:
            osm_type = 'node' if address['osm_id'][0] == 'n' else 'way' if address['osm_id'][0] == 'w' else 'relation'
            osm_link = f'https://www.openstreetmap.org/{osm_type}/{address["osm_id"][1:]}'
            osm_street = address['osm_street']
            osm_housenumber = address['osm_housenumber']
            if address['matching']:
                score = 1
            else:
                score = float(address['score'])
            distance = float(address['distance'])

        addresses.append({
            'rgz_kucni_broj_id': address['rgz_kucni_broj_id'],
            'rgz_ulica': address['rgz_ulica'],
            'rgz_kucni_broj': address['rgz_kucni_broj'],
            'location_url': location_url,
            'location_text': location_text,
            'conflated_osm_link': conflated_osm_link,
            'conflated_osm_street': conflated_osm_street,
            'conflated_osm_housenumber': conflated_osm_housenumber,
            'matching': address['matching'],
            'osm_link': osm_link,
            'osm_street': osm_street,
            'osm_housenumber': osm_housenumber,
            'score': score,
            'distance': distance
        })

    output = template.render(
        currentDate=current_date,
        currentDateSrb=current_date_srb,
        addresses=addresses,
        naselje=naselje,
        opstina_name=opstina_name,
        osm_files_new_addresses=osm_files_new_addresses,
        osm_files_matched_addresses=osm_files_matched_addresses)
    with open(naselje_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


def generate_opstina(env, osm_entities_cache, data_path, opstina_name, df_opstina, df_opstina_osm):
    report_path = os.path.join(data_path, 'report')
    template = env.get_template('opstina.html')
    current_date = datetime.date.today().strftime('%Y-%m-%d')
    current_date_srb = datetime.date.today().strftime('%d.%m.%Y')
    opstine_dir_path = os.path.join(report_path, 'opstine')
    if not os.path.exists(opstine_dir_path):
        os.mkdir(opstine_dir_path)
    opstina_html_path = os.path.join(opstine_dir_path, f'{opstina_name}.html')

    rgz_count = len(df_opstina)
    osm_count = len(df_opstina_osm)
    conflated_count = len(df_opstina[df_opstina['conflated_osm_id'].notnull()])
    matched_count = len(df_opstina[df_opstina['matching'] == True])
    partially_matched_count = len(df_opstina[(pd.notna(df_opstina.osm_id)) & (df_opstina.matching == False)])
    opstina = {
        'name': opstina_name,
        'name_norm': normalize_name(opstina_name),
        'rgz': rgz_count,
        'osm': osm_count,
        'conflated': conflated_count,
        'matched': matched_count,
        'partially_matched_count': partially_matched_count
    }

    if os.path.exists(opstina_html_path):
        # Don't regenerate anything if html exists
        print('skipping (exists)', end='')
        return opstina

    naselja = []

    for naselje_name, df_naselje in df_opstina.groupby('rgz_naselje'):
        rgz_count = len(df_naselje)
        conflated_count = len(df_naselje[df_naselje['conflated_osm_id'].notnull()])
        matched_count = len(df_naselje[df_naselje['matching'] == True])
        partially_matched_count = len(df_opstina[(pd.notna(df_opstina.osm_id)) & (df_opstina.matching == False)])
        naselje = {
            'name': naselje_name,
            'name_lat': cyr2lat(naselje_name),
            'rgz': rgz_count,
            'conflated': conflated_count,
            'matched': matched_count,
            'partially_matched_count': partially_matched_count
        }
        generate_naselje(env, osm_entities_cache, opstine_dir_path, opstina_name, naselje, df_naselje)

        naselja.append(naselje)

    output = template.render(
        currentDate=current_date,
        currentDateSrb=current_date_srb,
        naselja=naselja,
        opstina=opstina)
    with open(opstina_html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)
    print('OK', end='')
    return opstina


def generate_report(env, cwd, osm_entities_cache):
    template = env.get_template('report.html')
    data_path = os.path.join(cwd, 'data')

    print("Loading normalized street names mapping")
    load_mappings(data_path)

    osm_path = os.path.join(data_path, 'osm', 'csv')
    analysis_path = os.path.join(data_path, 'analysis')
    report_path = os.path.join(data_path, 'report')
    total_csvs = len(os.listdir(analysis_path))
    report_html_path = os.path.join(report_path, 'report.html')

    total = {
        'rgz': 0,
        'osm': 0,
        'conflated': 0,
        'matched': 0,
        'partially_matched_count': 0
    }
    opstine = []
    for i, file in enumerate(sorted(os.listdir(analysis_path))):
        if not file.endswith(".csv"):
            continue
        opstina_name = file[:-4]
        print(f"{i+1}/{total_csvs} Processing {opstina_name}...", end='')
        df_opstina = pd.read_csv(os.path.join(analysis_path, file), dtype={'conflated_osm_housenumber': object, 'osm_housenumber': object})
        df_opstina_osm = pd.read_csv(os.path.join(osm_path, file))
        opstina = generate_opstina(env, osm_entities_cache, data_path, opstina_name, df_opstina, df_opstina_osm)
        opstine.append(opstina)
        total['conflated'] += opstina['conflated']
        total['rgz'] += opstina['rgz']
        total['osm'] += opstina['osm']
        total['matched'] += opstina['matched']
        total['partially_matched_count'] += opstina['partially_matched_count']
        print()

    if os.path.exists(report_html_path):
        return

    current_date = datetime.date.today().strftime('%Y-%m-%d')
    current_date_srb = datetime.date.today().strftime('%d.%m.%Y')
    output = template.render(
        currentDate=current_date,
        currentDateSrb=current_date_srb,
        opstine=opstine,
        total=total)
    with open(report_html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


def main():
    current_date = datetime.date.today().strftime('%Y-%m-%d')
    current_date_srb = datetime.date.today().strftime('%d.%m.%Y')
    # TODO: sorting in some columns should be as numbers (distance, kucni broj)
    # TODO: address should be searchable with latin only
    env = Environment(loader=FileSystemLoader(searchpath='./templates'))
    env.globals.update(len=len, AddressInBuildingResolution=AddressInBuildingResolution)
    cwd = os.getcwd()

    data_path = os.path.join(cwd, 'data')
    print("Building cache of OSM entities")
    osm_entities_cache = build_osm_entities_cache(data_path)

    generate_report(env, cwd, osm_entities_cache)

    report_path = os.path.join(cwd, 'data/report')
    index_html_path = os.path.join(report_path, 'index.html')
    if os.path.exists(index_html_path):
        print("Page data/report/index.html already exists")
        return

    print("Generating data/report/index.html")
    template = env.get_template('index.html')
    output = template.render(
        currentDate=current_date,
        currentDateSrb=current_date_srb
    )
    with open(index_html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


if __name__ == '__main__':
    main()
