# -*- coding: utf-8 -*-

import datetime
import os

import geopandas as gpd
import osmium
import overpy
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from shapely import wkt

from common import AddressInBuildingResolution
from common import cyr2lat, normalize_name, normalize_name_latin, xml_escape, geojson2js
from street_mapping import StreetMapping


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


class OsmEntitiesOverpassCacheHandler:
    """
    Same thing as OsmEntitiesCacheHandler, just uses Overpass to create cache
    """
    def __init__(self, nodes, ways):
        self.nodes = list(nodes)
        self.ways = list(ways)
        self.nodes_cache = {}
        self.ways_cache = {}

    def apply_file(self, _):
        CHUNK_SIZE = 10000
        overpass_api = overpy.Overpass(url='http://localhost:12346/api/interpreter')
        for i in range(0, len(self.nodes) // CHUNK_SIZE + 1):
            print(f"Creating node cache - chunk {i + 1}/{len(self.nodes) // CHUNK_SIZE + 1}")
            chunk = self.nodes[i*CHUNK_SIZE:(i + 1) * CHUNK_SIZE]
            node_id_list = ','.join([str(n) for n in chunk])
            response = overpass_api.query(f"""
                [out:json];
                area["name"="Србија"]["admin_level"=2]->.c;
                (
                    node(id:{node_id_list});
                );
                out meta;
                // &contact=https://gitlab.com/osm-serbia/adresniregistar
            """)
            for n in response.nodes:
                if n.id not in self.nodes_cache:
                    self.nodes_cache[n.id] = {
                        'lat': n.lat,
                        'lon': n.lon,
                        'tags': n.tags.copy(),
                        'version': n.attributes['version']
                    }
        CHUNK_SIZE = 5000
        for i in range(0, len(self.ways) // CHUNK_SIZE + 1):
            print(f"Creating ways cache - chunk {i + 1}/{len(self.ways) // CHUNK_SIZE + 1}")
            chunk = self.ways[i*CHUNK_SIZE:(i + 1) * CHUNK_SIZE]
            way_id_list = ','.join([str(w) for w in chunk])
            response = overpass_api.query(f"""
                [out:json];
                area["name"="Србија"]["admin_level"=2]->.c;
                (
                    way(id:{way_id_list});
                );
                (._;>;);
                out meta;
                // &contact=https://gitlab.com/osm-serbia/adresniregistar
            """)
            for n in response.nodes:
                if n.id not in self.nodes_cache:
                    self.nodes_cache[n.id] = {
                        'lat': n.lat,
                        'lon': n.lon,
                        'tags': n.tags.copy(),
                        'version': n.attributes['version']
                    }
            for w in response.ways:
                if w.id not in self.ways_cache:
                    self.ways_cache[w.id] = {
                        'tags': w.tags.copy(),
                        'nodes': [n.id for n in w.nodes],
                        'version': w.attributes['version']
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
        if len(osm_entites_to_cache) > 0:
            nodes_to_cache += [int(n[1:]) for n in list(osm_entites_to_cache[osm_entites_to_cache.str.startswith('n')])]
            ways_to_cache += [int(w[1:]) for w in list(osm_entites_to_cache[osm_entites_to_cache.str.startswith('w')])]

    # Collects nodes and ways from qa/addresses_in_buildings_per_opstina.csv
    df_addresses_in_buildings_per_opstina = pd.read_csv(os.path.join(qa_path, 'addresses_in_buildings_per_opstina.csv'))
    df_addresses_in_buildings_per_opstina = df_addresses_in_buildings_per_opstina[df_addresses_in_buildings_per_opstina.resolution == AddressInBuildingResolution.MERGE_ADDRESS_TO_BUILDING.value]
    nodes_to_cache += [int(n[1:]) for n in list(df_addresses_in_buildings_per_opstina['osm_id_left']) if n[0] == 'n']
    ways_to_cache += [int(w[1:]) for w in list(df_addresses_in_buildings_per_opstina['osm_id_right']) if w[0] == 'w']

    if os.environ.get('AR_INCREMENTAL_UPDATE', None) == "1":
        print("Using overpass to build cache")
        osm_entities_cache = OsmEntitiesOverpassCacheHandler(set(nodes_to_cache), set(ways_to_cache))
    else:
        print("Using PBF to build cache")
        cwnh = CollectWayNodesHandler(set(ways_to_cache))
        cwnh.apply_file(pbf_file)

        osm_entities_cache = OsmEntitiesCacheHandler(set(nodes_to_cache).union(cwnh.nodes), set(ways_to_cache))

    osm_entities_cache.apply_file(pbf_file)
    return osm_entities_cache


def generate_osm_files_matched_addresses(context, opstina_dir_path, opstina_name, naselje, df_naselje):
    env = context['env']
    osm_entities_cache = context['osm_entities_cache']

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
                    'url': f'https://dina.openstreetmap.rs/ar/opstine/{opstina_name}/{filename}'
                }
            )
            old_counter = counter
            osm_nodes, osm_ways = [], []

        if address.osm_id[0] == 'n':
            counter = counter + 1
            node_id = int(address.osm_id[1:])
            entity = context['osm_entities_cache'].nodes_cache[node_id]
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
                'url': f'https://dina.openstreetmap.rs/ar/opstine/{opstina_name}/{filename}'
            }
        )

    return osm_files


def generate_osm_files_new_addresses(context, opstina_dir_path, opstina_name, naselje, df_naselje):
    env = context['env']
    street_mappings: StreetMapping = context['street_mappings']

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
                    'url': f'https://dina.openstreetmap.rs/ar/opstine/{opstina_name}/{filename}'
                }
            )
            osm_entities = []

        osm_entities.append({
            'id': 0 - (len(osm_entities) + 1),
            'lat': location_lat,
            'lon': location_lon,
            'street': street_mappings.get_name(address['rgz_ulica'], address['rgz_opstina']),
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
                'url': f'https://dina.openstreetmap.rs/ar/opstine/{opstina_name}/{filename}'
            }
        )

    return osm_files


def generate_naselje(context, opstina_dir_path, opstina_name, naselje, df_naselje):
    env = context['env']

    template = env.get_template('naselje.html')
    current_date = datetime.date.today().strftime('%Y-%m-%d')
    report_date = datetime.date.today().strftime('%d.%m.%Y %H:%M')
    opstina_name_norm = normalize_name(opstina_name)
    naselje_dir_path = os.path.join(opstina_dir_path, opstina_name_norm)
    if not os.path.exists(naselje_dir_path):
        os.mkdir(naselje_dir_path)

    osm_files_new_addresses, osm_files_matched_addresses = [], []
    if not context['incremental_update']:
        osm_files_new_addresses = generate_osm_files_new_addresses(context, opstina_dir_path, opstina_name_norm, naselje, df_naselje)
        osm_files_matched_addresses = generate_osm_files_matched_addresses(context, opstina_dir_path, opstina_name_norm, naselje, df_naselje)

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
        currentDate=context['dates']['short'],
        reportDate=context['dates']['report'],
        osmDataDate=context['dates']['osm_data'],
        realTime=context['incremental_update'],
        addresses=addresses,
        naselje=naselje,
        opstina_name=opstina_name,
        osm_files_new_addresses=osm_files_new_addresses,
        osm_files_matched_addresses=osm_files_matched_addresses)
    with open(naselje_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


def generate_opstina(context, opstina_name, df_opstina, df_opstina_osm):
    env = context['env']
    data_path = context['data_path']

    report_path = os.path.join(data_path, 'report')
    if context['incremental_update']:
        report_path = os.path.join(report_path, 'rt')

    template = env.get_template('opstina.html')
    opstine_dir_path = os.path.join(report_path, 'opstine')
    if not os.path.exists(opstine_dir_path):
        os.mkdir(opstine_dir_path)
    opstina_html_path = os.path.join(opstine_dir_path, f'{opstina_name}.html')

    rgz_count = len(df_opstina)
    osm_count = len(df_opstina_osm)
    conflated_count = len(df_opstina[df_opstina['conflated_osm_id'].notnull()])
    matched_count = len(df_opstina[(df_opstina['matching'] == True) & (pd.isna(df_opstina['conflated_osm_id']))])
    partially_matched_count = len(df_opstina[(pd.notna(df_opstina.osm_id)) & (df_opstina.matching == False) & (pd.isna(df_opstina['conflated_osm_id']))])
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
        return opstina, []

    naselja = []

    for naselje_name, df_naselje in df_opstina.groupby('rgz_naselje'):
        rgz_count = len(df_naselje)
        conflated_count = len(df_naselje[df_naselje['conflated_osm_id'].notnull()])
        matched_count = len(df_naselje[(df_naselje['matching'] == True) & (pd.isna(df_naselje['conflated_osm_id']))])
        partially_matched_count = len(df_opstina[(pd.notna(df_opstina.osm_id)) & (df_opstina.matching == False) & (pd.isna(df_naselje['conflated_osm_id']))])
        naselje = {
            'name': naselje_name,
            'opstina': opstina,
            'name_lat': cyr2lat(naselje_name),
            'rgz': rgz_count,
            'conflated': conflated_count,
            'matched': matched_count,
            'partially_matched_count': partially_matched_count
        }
        generate_naselje(context, opstine_dir_path, opstina_name, naselje, df_naselje)

        naselja.append(naselje)

    # Generate naselja js
    naselja_js_path = os.path.join(opstine_dir_path, f'{opstina["name_norm"]}.js')
    if os.path.exists(naselja_js_path):
        return opstina, []

    df_calc_naselja = pd.DataFrame(naselja)
    df_calc_naselja['ratio'] = df_calc_naselja.apply(lambda row: 100 * row.conflated / row.rgz, axis=1)

    gdf_naselja = context['gdf_naselja']
    gdf_naselje = gdf_naselja[gdf_naselja.opstina_imel == opstina_name]

    gdf_naselje = gdf_naselje.merge(df_calc_naselja[['name_lat', 'ratio']], left_on='naselje_imel', right_on='name_lat')
    assert len(gdf_naselje) == len(df_calc_naselja)
    gdf_naselje.drop(['opstina_imel', 'name_lat'], inplace=True, axis=1)
    gdf_naselje.to_file(naselja_js_path, driver='GeoJSON')
    opstina['bounds'] = gdf_naselje.unary_union.bounds

    geojson2js(naselja_js_path, 'naselja')

    output = template.render(
        currentDate=context['dates']['short'],
        reportDate=context['dates']['report'],
        osmDataDate=context['dates']['osm_data'],
        realTime=context['incremental_update'],
        showAllNaselja=False,
        naselja=naselja,
        opstina=opstina)
    with open(opstina_html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)

    print('OK', end='')
    return opstina, naselja


def generate_all_naselja(context, total, all_naselja):
    env = context['env']
    data_path = context['data_path']

    report_path = os.path.join(data_path, 'report')
    if context['incremental_update']:
        report_path = os.path.join(report_path, 'rt')
    template = env.get_template('opstina.html')
    all_naselja_html_path = os.path.join(report_path, 'all_naselja.html')

    if os.path.exists(all_naselja_html_path):
        print('Skipping all_naselja.html, already exist')
        return

    output = template.render(
        currentDate=context['dates']['short'],
        reportDate=context['dates']['report'],
        osmDataDate=context['dates']['osm_data'],
        realTime=context['incremental_update'],
        showAllNaselja=True,
        naselja=all_naselja,
        opstina=total)
    with open(all_naselja_html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


def generate_report(context):
    env = context['env']

    template = env.get_template('report.html')

    data_path = context['data_path']

    osm_path = os.path.join(data_path, 'osm', 'csv')
    rgz_path = os.path.join(data_path, 'rgz')
    analysis_path = os.path.join(data_path, 'analysis')
    report_path = os.path.join(data_path, 'report')
    if context['incremental_update']:
        report_path = os.path.join(report_path, 'rt')

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
    all_naselja = []
    for i, file in enumerate(sorted(os.listdir(analysis_path))):
        if not file.endswith(".csv"):
            continue
        opstina_name = file[:-4]
        print(f"{i+1}/{total_csvs} Processing {opstina_name}...", end='')
        df_opstina = pd.read_csv(os.path.join(analysis_path, file), dtype={'conflated_osm_housenumber': object, 'osm_housenumber': object})
        df_opstina_osm = pd.read_csv(os.path.join(osm_path, file), dtype='unicode')
        opstina, naselja = generate_opstina(context, opstina_name, df_opstina, df_opstina_osm)
        all_naselja += naselja
        opstine.append(opstina)
        total['conflated'] += opstina['conflated']
        total['rgz'] += opstina['rgz']
        total['osm'] += opstina['osm']
        total['matched'] += opstina['matched']
        total['partially_matched_count'] += opstina['partially_matched_count']
        total['bounds'] = (0, 0, 0, 0)
        print()

    if not os.path.exists(report_html_path):
        output = template.render(
            currentDate=context['dates']['short'],
            reportDate=context['dates']['report'],
            osmDataDate=context['dates']['osm_data'],
            realTime=context['incremental_update'],
            opstine=opstine,
            total=total)
        with open(report_html_path, 'w', encoding='utf-8') as fh:
            fh.write(output)

    generate_all_naselja(context, total, all_naselja)

    opstine_js_path = os.path.join(report_path, 'opstine.js')
    if os.path.exists(opstine_js_path):
        return

    df_calc_opstine = pd.DataFrame(opstine)
    df_calc_opstine['ratio'] = df_calc_opstine.apply(lambda row: 100 * row.conflated / row.rgz, axis=1)
    df_opstine = pd.read_csv(os.path.join(rgz_path, 'opstina.csv'))
    df_opstine['geometry'] = df_opstine.wkt.apply(wkt.loads)
    df_opstine = df_opstine[~df_opstine.okrug_sifra.isin([25, 26, 27, 28, 29])]  # remove kosovo
    df_opstine = df_opstine.merge(df_calc_opstine[['name', 'ratio']], left_on='opstina_imel', right_on='name')
    df_opstine.drop(['name', 'opstina_maticni_broj', 'opstina_ime', 'opstina_povrsina', 'okrug_sifra', 'okrug_ime', 'okrug_imel', 'wkt'], inplace=True, axis=1)
    gdf_opstine = gpd.GeoDataFrame(df_opstine, geometry='geometry', crs="EPSG:32634")
    gdf_opstine.to_crs("EPSG:4326", inplace=True)
    gdf_opstine['geometry'] = gdf_opstine.simplify(tolerance=0.0005)
    gdf_opstine.to_file(opstine_js_path, driver='GeoJSON')

    geojson2js(opstine_js_path, 'opstine')


def load_naselja_boundaries(rgz_path):
    df_naselja = pd.read_csv(os.path.join(rgz_path, 'naselje.csv'))
    df_naselja['geometry'] = df_naselja.wkt.apply(wkt.loads)
    df_naselja.drop(['objectid', 'naselje_maticni_broj', 'naselje_ime', 'naselje_povrsina', 'opstina_maticni_broj',
                     'opstina_ime', 'wkt'], inplace=True, axis=1)
    gdf_naselja = gpd.GeoDataFrame(df_naselja, geometry='geometry', crs="EPSG:32634")
    gdf_naselja.to_crs("EPSG:4326", inplace=True)
    gdf_naselja['geometry'] = gdf_naselja.simplify(tolerance=0.0001)
    return gdf_naselja


def main():
    # TODO: sorting in some columns should be as numbers (distance, kucni broj)
    # TODO: address should be searchable with latin only
    env = Environment(loader=FileSystemLoader(searchpath='./templates'))
    env.globals.update(len=len, AddressInBuildingResolution=AddressInBuildingResolution)
    cwd = os.getcwd()

    data_path = os.path.join(cwd, 'data')
    rgz_path = os.path.join(data_path, 'rgz')

    running_file = os.path.join(data_path, 'running')
    if not os.path.exists(running_file):
        raise Exception("File data/running missing, no way to determine date when OSM data was retrived")
    with open(running_file, 'r') as file:
        file_content = file.read().rstrip()
        osm_data_timestamp = datetime.datetime.fromisoformat(file_content).strftime('%d.%m.%Y %H:%M')

    incremental_update = False
    if os.environ.get('AR_INCREMENTAL_UPDATE', None) == "1":
        incremental_update = True

    osm_entities_cache = None
    if not incremental_update:
        print("Building cache of OSM entities")
        osm_entities_cache = build_osm_entities_cache(data_path)

    print("Loading normalized street names mapping")
    street_mappings = StreetMapping(cwd)

    print("Loading boundaries of naselja")
    gdf_naselja = load_naselja_boundaries(rgz_path)

    context = {
        'env': env,
        'cwd': cwd,
        'data_path': data_path,
        'incremental_update': incremental_update,
        'dates': {
            'short': datetime.date.today().strftime('%Y-%m-%d'),
            'report': datetime.datetime.now().strftime('%d.%m.%Y %H:%M'),
            'osm_data': osm_data_timestamp
        },
        'osm_entities_cache': osm_entities_cache,
        'street_mappings': street_mappings,
        'gdf_naselja': gdf_naselja
    }
    generate_report(context)

    if incremental_update:
        return

    report_path = os.path.join(cwd, 'data/report')
    index_html_path = os.path.join(report_path, 'index.html')
    if os.path.exists(index_html_path):
        print(f"Page {os.path.relpath(index_html_path)} already exists")
        return

    print(f"Generating {os.path.relpath(index_html_path)}")
    template = env.get_template('index.html')
    output = template.render(
        currentDate=context['dates']['short'],
        reportDate=context['dates']['report'],
        osmDataDate=context['dates']['osm_data']
    )
    with open(index_html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


if __name__ == '__main__':
    main()
