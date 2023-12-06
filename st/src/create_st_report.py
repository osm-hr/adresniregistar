# -*- coding: utf-8 -*-

import datetime
import json
import os
import urllib
from itertools import chain
import osmium

import geojson
import geopandas as gpd
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from shapely import wkt

from common import cyr2lat, normalize_name, geojson2js, xml_escape, OsmEntitiesCacheHandler
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
            ways_to_cache_string = list(chain(*[w.split(',') for w in list(osm_entites_to_cache[osm_entites_to_cache.str.startswith('w')])]))
            ways_to_cache += [int(w[1:]) for w in ways_to_cache_string]

    print("Using PBF to build cache")

    cwnh = CollectWayNodesHandler(set(ways_to_cache))
    cwnh.apply_file(pbf_file)

    osm_entities_cache = OsmEntitiesCacheHandler(set(cwnh.nodes), set(ways_to_cache))

    osm_entities_cache.apply_file(pbf_file)
    return osm_entities_cache


def generate_osm_files_matched_streets(context, opstina_dir_path, opstina_name, naselje, df_naselje):
    env = context['env']
    osm_entities_cache = context['osm_entities_cache']

    naselje_dir_path = os.path.join(opstina_dir_path, opstina_name)
    split_limit = 10

    template = env.get_template('matched_streets.osm')
    osm_files = []
    min_lat, min_lon, max_lat, max_lon = 90, 180, -90, 0
    osm_ways = []
    old_counter = 0
    counter = 0
    only_matched_addresses = df_naselje[pd.notna(df_naselje.found_osm_id)]
    for _, address in only_matched_addresses.sort_values(['rgz_ulica']).iterrows():
        found_any = False
        flushed_if_needed = False
        for found_way_id, name_match in zip(address.found_osm_id.split(','), address.name_match.split(',')):
            if name_match != '1':
                continue

            if found_way_id[0] == 'n':
                print(f"Encountered node {found_way_id}, not expecting this... ", end='')
                continue
            if found_way_id[0] == 'r':
                print(f"Encountered relation {found_way_id}, had to be merged manually... ", end='')
                continue

            way_id = int(found_way_id[1:])
            if way_id not in osm_entities_cache.ways_cache:
                continue

            if counter > 0 and counter % split_limit == 0 and not flushed_if_needed:
                output = template.render(osm_ways=osm_ways, min_lat=min_lat, min_lon=min_lon, max_lat=max_lat, max_lon=max_lon)
                filename = f'{normalize_name(naselje["name_lat"])}-matched-{counter}.osm'
                osm_file_path = os.path.join(naselje_dir_path, filename)
                with open(osm_file_path, 'w', encoding='utf-8') as fh:
                    fh.write(output)
                osm_files.append(
                    {
                        'name': f'{old_counter + 1}-{counter}',
                        'url': f'https://dina.openstreetmap.rs/st/opstine/{opstina_name}/{filename}'
                    }
                )
                old_counter = counter
                osm_ways = []
                min_lat, min_lon, max_lat, max_lon = 90, 180, -90, 0
                flushed_if_needed = True

            found_any = True
            entity = osm_entities_cache.ways_cache[way_id]
            new_tags = dict(entity['tags'], **{'ref:RS:ulica': str(address.rgz_ulica_mb)})
            osm_ways.append({
                'id': way_id,
                'tags': {k: xml_escape(v) for k, v in new_tags.items()},
                'nodes': entity['nodes'],
                'version': entity['version']
            })
            for node_id in entity['nodes']:
                if node_id not in osm_entities_cache.nodes_cache:
                    continue
                found_node = osm_entities_cache.nodes_cache[node_id]
                if found_node['lon'] < min_lon:
                    min_lon = found_node['lon']
                if found_node['lon'] > max_lon:
                    max_lon = found_node['lon']
                if found_node['lat'] < min_lat:
                    min_lat = found_node['lat']
                if found_node['lat'] > max_lat:
                    max_lat = found_node['lat']

        if found_any:
            counter = counter + 1

    # Final write
    if len(osm_ways) > 0:
        output = template.render(osm_ways=osm_ways, min_lat=min_lat, min_lon=min_lon, max_lat=max_lat, max_lon=max_lon)
        filename = f'{normalize_name(naselje["name_lat"])}-matched-{counter}.osm'
        osm_file_path = os.path.join(naselje_dir_path, filename)
        with open(osm_file_path, 'w', encoding='utf-8') as fh:
            fh.write(output)
        osm_files.append(
            {
                'name': f'{old_counter + 1}-{counter}',
                'url': f'https://dina.openstreetmap.rs/st/opstine/{opstina_name}/{filename}'
            }
        )

    return osm_files


def generate_naselje(context, opstina_dir_path, opstina_name, naselje, df_naselje):
    env = context['env']

    template = env.get_template('naselje.html.tpl')
    opstina_name_norm = normalize_name(opstina_name)
    naselje_dir_path = os.path.join(opstina_dir_path, opstina_name_norm)
    if not os.path.exists(naselje_dir_path):
        os.mkdir(naselje_dir_path)

    osm_files_matched_streets = generate_osm_files_matched_streets(context, opstina_dir_path, opstina_name_norm, naselje, df_naselje)

    naselje_path = os.path.join(naselje_dir_path, f'{naselje["name_lat"]}.html')

    streets = []
    for _, address in df_naselje.iterrows():
        conflated_ways, found_ways = [], []
        max_conflated_osm_way_length = -1
        if pd.notna(address['conflated_osm_id']):
            conflated_osm_ids = address['conflated_osm_id'].split(',')
            conflated_osm_way_lengths = address['conflated_osm_way_length'].split(',')
            assert len(conflated_osm_ids) == len(conflated_osm_way_lengths)
            for conflated_osm_id, conflated_osm_way_length in zip(conflated_osm_ids, conflated_osm_way_lengths):
                osm_type = 'node' if conflated_osm_id[0] == 'n' else 'way' if conflated_osm_id[0] == 'w' else 'relation'
                conflated_ways.append({
                    'osm_id': conflated_osm_id,
                    'osm_link': f'https://www.openstreetmap.org/{osm_type}/{conflated_osm_id[1:]}',
                    'conflated_osm_way_length': round(float(conflated_osm_way_length), 2)
                })
            max_conflated_osm_way_length = max([way['conflated_osm_way_length'] for way in conflated_ways])
        found_max_found_intersection = -1
        if pd.notna(address['found_osm_id']):
            found_osm_ids = address['found_osm_id'].split(',')
            name_matches = [True if x == '1' else False for x in address['name_match'].split(',')]
            norm_name_matches = [True if x == '1' else False for x in address['norm_name_match'].split(',')]
            osm_names = json.loads(address['osm_name'])
            found_intersections = str(address['found_intersection']).split(',')
            found_osm_way_lengths = str(address['found_osm_way_length']).split(',')
            assert len(found_osm_ids) == len(found_intersections)
            assert len(found_osm_ids) == len(found_osm_way_lengths)
            assert len(found_osm_ids) == len(name_matches)
            assert len(found_osm_ids) == len(norm_name_matches)
            assert len(found_osm_ids) == len(osm_names)
            for found_osm_id, found_intersection, found_osm_way_length, osm_name, name_match, norm_name_match in zip(found_osm_ids, found_intersections, found_osm_way_lengths, osm_names, name_matches, norm_name_matches):
                osm_type = 'node' if found_osm_id[0] == 'n' else 'way' if found_osm_id[0] == 'w' else 'relation'
                osm_label = osm_name if osm_name != '' else found_osm_id
                found_ways.append({
                    'osm_name': osm_label,
                    'osm_link': f'https://www.openstreetmap.org/{osm_type}/{found_osm_id[1:]}',
                    'found_intersection': round(100.0 * float(found_intersection), 2),
                    'found_osm_way_length': found_osm_way_length,
                    'name_match': name_match,
                    'norm_name_match': norm_name_match,
                    'wrong_name': osm_name != '' and not name_match and not norm_name_match
                })
            found_max_found_intersection = max([way['found_intersection'] for way in found_ways])

        rgz_geojson = geojson.Feature(geometry=address['rgz_geometry'], properties={"stroke": "#c01c28", "stroke-width": 4, "stroke-opacity": 1})
        if pd.notna(address['osm_geometry']):
            osm_geojson = geojson.Feature(geometry=wkt.loads(address['osm_geometry']), properties={"stroke": "#1c71d8", "stroke-width": 3, "stroke-opacity": 1})
            both_geojson = geojson.FeatureCollection([rgz_geojson, osm_geojson])
        else:
            # both_geojson = rgz_geojson
            both_geojson = geojson.FeatureCollection([rgz_geojson])
        geojson_data = urllib.parse.quote(geojson.dumps(both_geojson))
        rgz_geojson_url = f"http://geojson.io/#data=data:application/json,{geojson_data}"
        streets.append({
            'rgz_ulica_mb': address['rgz_ulica_mb'],
            'rgz_ulica': address['rgz_ulica'],
            'rgz_ulica_proper': address['rgz_ulica_proper'] if pd.notna(address['rgz_ulica_proper']) else '',
            'rgz_geojson_url': rgz_geojson_url,
            'rgz_way_length': round(address['rgz_way_length']),
            'conflated_ways': conflated_ways,
            'conflated_max_error': round(address['conflated_max_error']) if pd.notna(address['conflated_max_error']) else None,
            'max_conflated_osm_way_length': max_conflated_osm_way_length,
            'found_ways': found_ways,
            'found_max_found_intersection': found_max_found_intersection,
            'is_circle': address['is_circle'],
        })

    output = template.render(
        currentDate=context['dates']['short'],
        reportDate=context['dates']['report'],
        osmDataDate=context['dates']['osm_data'],
        streets=streets,
        naselje=naselje,
        opstina_name=opstina_name,
        osm_files_matched_streets=osm_files_matched_streets
    )
    with open(naselje_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


def generate_opstina(context, opstina_name, df_opstina, df_opstina_osm):
    env = context['env']
    data_path = context['data_path']

    report_path = os.path.join(data_path, 'report')

    template = env.get_template('opstina.html.tpl')
    opstine_dir_path = os.path.join(report_path, 'opstine')
    if not os.path.exists(opstine_dir_path):
        os.mkdir(opstine_dir_path)
    opstina_html_path = os.path.join(opstine_dir_path, f'{opstina_name}.html')

    df_opstina_no_circles = df_opstina[~df_opstina.is_circle]
    rgz_count = len(df_opstina_no_circles)
    rgz_length = df_opstina_no_circles['rgz_way_length'].sum()
    # Condensed way to sum all split ways into one and sum them altogether
    conflated_length = round(sum([i for i in [sum([float(i) for i in x.split(',')]) if type(x)==str else x for x in df_opstina['conflated_osm_way_length']] if pd.notna(i)]), 2)
    found_length = round(sum([i for i in [sum([float(i) for i in x.split(',')]) if type(x)==str else x for x in df_opstina['found_osm_way_length']] if pd.notna(i)]), 2)
    opstina = {
        'name': opstina_name,
        'name_norm': normalize_name(opstina_name),
        'rgz': rgz_count,
        'rgz_length': rgz_length,
        'conflated_length': conflated_length,
        'found_length': found_length,
        'notfound_length': max(rgz_length - (conflated_length + found_length), 0)
    }

    if os.path.exists(opstina_html_path):
        # Don't regenerate anything if html exists
        print('skipping (exists)', end='')
        return opstina, []

    naselja = []

    for naselje_name, df_naselje in df_opstina.groupby('rgz_naselje'):
        df_naselje_no_circles = df_naselje[~df_naselje.is_circle]
        rgz_count = len(df_naselje_no_circles)
        rgz_length = df_naselje_no_circles['rgz_way_length'].sum()
        conflated_length = round(sum([i for i in [sum([float(i) for i in x.split(',')]) if type(x)==str else x for x in df_naselje['conflated_osm_way_length']] if pd.notna(i)]), 2)
        found_length = round(sum([i for i in [sum([float(i) for i in x.split(',')]) if type(x)==str else x for x in df_naselje['found_osm_way_length']] if pd.notna(i)]), 2)
        naselje = {
            'name': naselje_name,
            'opstina': opstina,
            'name_lat': cyr2lat(naselje_name),
            'rgz': rgz_count,
            'rgz_length': rgz_length,
            'conflated_length': conflated_length,
            'found_length': found_length,
            'notfound_length': max(rgz_length - (conflated_length + found_length), 0)
        }
        generate_naselje(context, opstine_dir_path, opstina_name, naselje, df_naselje)

        naselja.append(naselje)

    # Generate naselja js
    naselja_js_path = os.path.join(opstine_dir_path, f'{opstina["name_norm"]}.js')
    if os.path.exists(naselja_js_path):
        return opstina, []

    df_calc_naselja = pd.DataFrame(naselja)
    df_calc_naselja['ratio'] = df_calc_naselja.apply(lambda row: min(100 * row.conflated_length / row.rgz_length, 100), axis=1)

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
        showAllNaselja=False,
        naselja=naselja,
        opstina=opstina)
    with open(opstina_html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)

    print('OK', end='')
    return opstina, naselja


def generate_report(context):
    env = context['env']

    template = env.get_template('report.html.tpl')

    data_path = context['data_path']

    osm_path = os.path.join(data_path, 'osm', 'csv')
    rgz_path = os.path.join(data_path, 'rgz')
    analysis_path = os.path.join(data_path, 'analysis')
    report_path = os.path.join(data_path, 'report')

    total_csvs = len(os.listdir(analysis_path))
    report_html_path = os.path.join(report_path, 'report.html')

    total = {
        'rgz': 0,
        'rgz_length': 0,
        'conflated_length': 0,
        'found_length': 0,
        'notfound_length': 0,
    }
    opstine = []
    all_naselja = []
    for i, file in enumerate(sorted(os.listdir(analysis_path))):
        if not file.endswith(".csv"):
            continue
        opstina_name = file[:-4]
        print(f"{i+1}/{total_csvs} Processing {opstina_name}...", end='')
        df_opstina = pd.read_csv(os.path.join(analysis_path, file), dtype={'conflated_osm_way_length': object})
        df_opstina['rgz_geometry'] = df_opstina.rgz_geometry.apply(wkt.loads)
        gdf_opstina = gpd.GeoDataFrame(df_opstina, geometry='rgz_geometry', crs="EPSG:4326")
        df_opstina_osm = pd.read_csv(os.path.join(osm_path, file), dtype='unicode')
        opstina, naselja = generate_opstina(context, opstina_name, gdf_opstina, df_opstina_osm)
        all_naselja += naselja
        opstine.append(opstina)
        total['rgz'] += opstina['rgz']
        total['rgz_length'] += opstina['rgz_length']
        total['conflated_length'] += opstina['conflated_length']
        total['found_length'] += opstina['found_length']
        total['notfound_length'] += opstina['notfound_length']
        total['bounds'] = (0, 0, 0, 0)
        print()

    if not os.path.exists(report_html_path):
        output = template.render(
            currentDate=context['dates']['short'],
            reportDate=context['dates']['report'],
            osmDataDate=context['dates']['osm_data'],
            opstine=opstine,
            total=total)
        with open(report_html_path, 'w', encoding='utf-8') as fh:
            fh.write(output)

    opstine_js_path = os.path.join(report_path, 'opstine.js')
    if os.path.exists(opstine_js_path):
        return

    df_calc_opstine = pd.DataFrame(opstine)
    df_calc_opstine['ratio'] = df_calc_opstine.apply(lambda row: 100 * row.conflated_length / row.rgz_length, axis=1)
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
    env = Environment(loader=FileSystemLoader(searchpath='./templates'))
    env.globals.update(len=len)
    cwd = os.getcwd()

    data_path = os.path.join(cwd, 'data')
    rgz_path = os.path.join(data_path, 'rgz')

    running_file = os.path.join(data_path, 'running')
    if not os.path.exists(running_file):
        raise Exception("File data/running missing, no way to determine date when OSM data was retrived")
    with open(running_file, 'r') as file:
        file_content = file.read().rstrip()
        osm_data_timestamp = datetime.datetime.fromisoformat(file_content).strftime('%d.%m.%Y %H:%M')

    print("Building cache of OSM entities")
    osm_entities_cache = build_osm_entities_cache(data_path)

    print("Loading normalized street names mapping")
    street_mappings = StreetMapping(os.path.join(cwd, '..', 'ar'))

    print("Loading boundaries of naselja")
    gdf_naselja = load_naselja_boundaries(rgz_path)

    context = {
        'env': env,
        'cwd': cwd,
        'data_path': data_path,
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

    report_path = os.path.join(cwd, 'data/report')
    index_html_path = os.path.join(report_path, 'index.html')
    if os.path.exists(index_html_path):
        print(f"Page {os.path.relpath(index_html_path)} already exists")
        return

    print(f"Generating {os.path.relpath(index_html_path)}")
    template = env.get_template('index.html.tpl')
    output = template.render(
        currentDate=context['dates']['short'],
        reportDate=context['dates']['report'],
        osmDataDate=context['dates']['osm_data']
    )
    with open(index_html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


if __name__ == '__main__':
    main()
