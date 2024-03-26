# -*- coding: utf-8 -*-

import datetime
import json
import os

import pandas as pd
from jinja2 import Environment, FileSystemLoader

from common import AddressInBuildingResolution
from common import normalize_name, normalize_name_latin, xml_escape, housenumber_to_float
from create_report import build_osm_entities_cache
from street_mapping import StreetMapping


def generate_osm_files_move_address_to_building(context, report_qa_address_path, opstina_name, df_opstina):
    env = context['env']
    osm_entities_cache = context['osm_entities_cache']

    split_limit = 100
    opstina_name_norm = normalize_name(opstina_name)

    template = env.get_template('move_address_to_building.osm')
    osm_files = []
    osm_nodes, osm_nodes_to_delete, osm_ways = [], [], []
    old_counter = 0
    counter = 0
    df_buildings = df_opstina[df_opstina.resolution == AddressInBuildingResolution.MERGE_ADDRESS_TO_BUILDING]
    for osm_id_right, df_building in df_buildings.sort_values(['osm_street_left', 'osm_housenumber_left']).groupby('osm_id_right'):
        if osm_id_right[0] == 'n':
            print(f"Encountered node {osm_id_right}, had to be merged manually... ", end='')
            continue
        if osm_id_right[0] == 'r':
            print(f"Encountered relation {osm_id_right}, had to be merged manually... ", end='')
            continue

        if counter > 0 and counter % split_limit == 0:
            output = template.render(osm_nodes=osm_nodes, osm_nodes_to_delete=osm_nodes_to_delete, osm_ways=osm_ways)
            filename = f'{opstina_name_norm}-address_to_building-{counter}.osm'
            osm_file_path = os.path.join(report_qa_address_path, filename)
            with open(osm_file_path, 'w', encoding='utf-8') as fh:
                fh.write(output)
            osm_files.append(
                {
                    'name': f'{old_counter+1}-{counter}',
                    'url': f'https://dina.openstreetmap.rs/ar/qa_addresses/{filename}'
                }
            )
            old_counter = counter
            osm_nodes, osm_nodes_to_delete, osm_ways = [], [], []

        # Collect all tags from all nodes. If there are multiple values for same tag, add them all separated with ';'
        node_tags = {}
        for _, address in df_building.iterrows():
            node_id = int(address['osm_id_left'][1:])
            if node_id not in osm_entities_cache.nodes_cache:
                print(f"Node {node_id} seems deleted, skipping one building to move address")
                continue
            entity = osm_entities_cache.nodes_cache[node_id]
            osm_nodes_to_delete.append({
                'id': node_id,
                'version': entity['version'],
                'tags': {k: xml_escape(v) for k, v in entity['tags'].items()},
                'lat': entity['lat'],
                'lon': entity['lon'],
            })
            for k, v in entity['tags'].items():
                if k not in node_tags:
                    node_tags[k] = v
                all_values = node_tags[k].split(';')
                if v not in all_values:
                    node_tags[k] = node_tags[k] + ';' + v

        way_id = int(osm_id_right[1:])
        entity = osm_entities_cache.ways_cache[way_id]
        counter = counter + 1

        # Merge tags from node(s) to building tags. If tag exist in building, add them separated with ';'
        new_tags = entity['tags']
        for k, v in node_tags.items():
            if k not in new_tags:
                new_tags[k] = v
            if k.startswith('addr:') or k in ['building', 'building:levels', 'roof:levels', 'survey:date']:
                # Don't add multiple values for these tags, just keep whatever is on the building
                continue
            all_values = new_tags[k].split(';')
            if v not in all_values:
                new_tags[k] = new_tags[k] + ';' + v

        osm_ways.append({
            'id': way_id,
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
    if len(osm_nodes) > 0 or len(osm_nodes_to_delete) > 0 or len(osm_ways) > 0:
        output = template.render(osm_nodes=osm_nodes, osm_nodes_to_delete=osm_nodes_to_delete, osm_ways=osm_ways)
        filename = f'{opstina_name_norm}-address_to_building-{counter}.osm'
        osm_file_path = os.path.join(report_qa_address_path, filename)
        with open(osm_file_path, 'w', encoding='utf-8') as fh:
            fh.write(output)
        osm_files.append(
            {
                'name': f'{old_counter + 1}-{counter}',
                'url': f'https://dina.openstreetmap.rs/ar/qa_addresses/{filename}'
            }
        )

    return osm_files


def generate_qa_duplicated_refs(context):
    env = context['env']
    cwd = context['cwd']

    qa_path = os.path.join(cwd, 'data/qa')
    report_path = os.path.join(cwd, 'data/report')
    json_file_path = os.path.join(qa_path, 'duplicated_refs.json')
    html_path = os.path.join(report_path, 'duplicated_refs.html')
    if os.path.exists(html_path):
        print("Page data/report/duplicated_refs.html already exists")
        return

    print("Generating data/report/duplicated_refs.html")
    with open(json_file_path, encoding='utf-8') as fh:
        addresses = json.load(fh)

    duplicates = []
    for address in addresses:
        links = []
        for dup in address['duplicates']:
            street_name = dup['tags']['addr:street'] if 'addr:street' in dup['tags'] else ''
            housenumber = dup['tags']['addr:housenumber'] if 'addr:housenumber' in dup['tags'] else ''
            links.append({
                'href': f'https://www.openstreetmap.org/{dup["type"]}/{dup["id"]}',
                'name': f'{street_name} {housenumber}' if len(street_name) > 0 or len(housenumber) > 0 else f'{dup["type"]} {dup["id"]}'
            })
        duplicates.append({
            'id': address['ref:RS:kucni_broj'],
            'opstina': address['opstina_imel'],
            'links': links
        })
    template = env.get_template('qa/duplicated_refs.html.tpl')
    output = template.render(
        duplicates=duplicates,
        currentDate=context['dates']['short'],
        reportDate=context['dates']['report'],
        rgzDataDate=context['dates']['rgz_data'],
        osmDataDate=context['dates']['osm_data']
    )
    with open(html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


def generate_addresses_in_buildings(context):
    env = context['env']
    cwd = context['cwd']

    analysis_path = os.path.join(cwd, 'data/analysis')
    qa_path = os.path.join(cwd, 'data/qa')
    report_path = os.path.join(cwd, 'data/report')
    report_qa_address_path = os.path.join(report_path, 'qa_addresses')
    html_path = os.path.join(report_path, 'addresses_in_buildings.html')
    template = env.get_template('qa/addresses_in_buildings_opstina.html.tpl')

    if not os.path.exists(report_qa_address_path):
        os.mkdir(report_qa_address_path)

    df_addresses_in_buildings = pd.read_csv(os.path.join(qa_path, 'addresses_in_buildings_per_opstina.csv'))
    df_addresses_in_buildings['resolution'] = df_addresses_in_buildings['resolution'].apply(lambda x: AddressInBuildingResolution(x))

    opstine = []
    total = {
        'count': 0
    }
    resolution_stats = {
        AddressInBuildingResolution.NO_ACTION: 0,
        AddressInBuildingResolution.MERGE_POI_TO_BUILDING: 0,
        AddressInBuildingResolution.MERGE_ADDRESS_TO_BUILDING: 0,
        AddressInBuildingResolution.COPY_POI_ADDRESS_TO_BUILDING: 0,
        AddressInBuildingResolution.ATTACH_ADDRESSES_TO_BUILDING: 0,
        AddressInBuildingResolution.REMOVE_ADDRESS_FROM_BUILDING: 0,
        AddressInBuildingResolution.ADDRESSES_NOT_MATCHING: 0,
        AddressInBuildingResolution.CASE_TOO_COMPLEX: 0,
        AddressInBuildingResolution.BUILDING_IS_NODE: 0,
        AddressInBuildingResolution.NOTE_PRESENT: 0
    }

    for opstina_name, df_opstina in df_addresses_in_buildings.sort_values('opstina_imel').groupby('opstina_imel'):
        count = len(df_opstina['osm_id_right'].value_counts())
        total['count'] += count
        opstine.append({
            'name': opstina_name,
            'count': count
        })
        addresses = []
        opstina_resolution_stats = {
            AddressInBuildingResolution.NO_ACTION: 0,
            AddressInBuildingResolution.MERGE_POI_TO_BUILDING: 0,
            AddressInBuildingResolution.MERGE_ADDRESS_TO_BUILDING: 0,
            AddressInBuildingResolution.COPY_POI_ADDRESS_TO_BUILDING: 0,
            AddressInBuildingResolution.ATTACH_ADDRESSES_TO_BUILDING: 0,
            AddressInBuildingResolution.REMOVE_ADDRESS_FROM_BUILDING: 0,
            AddressInBuildingResolution.ADDRESSES_NOT_MATCHING: 0,
            AddressInBuildingResolution.CASE_TOO_COMPLEX: 0,
            AddressInBuildingResolution.BUILDING_IS_NODE: 0,
            AddressInBuildingResolution.NOTE_PRESENT: 0
        }

        opstina_html_path = os.path.join(report_qa_address_path, f'{opstina_name}.html')
        if os.path.exists(opstina_html_path):
            print(f"Page data/report/qa_addresses/{opstina_name}.html already exists")
            continue

        print(f"Generating data/report/qa_addresses/{opstina_name}.html")

        osm_files_move_address_to_building = generate_osm_files_move_address_to_building(context, report_qa_address_path, opstina_name, df_opstina)

        for osm_id_right, df_address in df_opstina.groupby('osm_id_right'):
            building_address = ''
            street = df_address['osm_street_right'].values[0]
            house_number = df_address['osm_housenumber_right'].values[0]
            if pd.notna(street) or pd.notna(house_number):
                building_address = f"{street if pd.notna(street) else ''} {house_number if pd.notna(house_number) else ''}"

            osm_type = 'way' if osm_id_right[0] == 'w' else 'relation' if osm_id_right[0] == 'r' else 'node'
            resolution = df_address['resolution'].iloc[0]
            address = {
                'building_osm_link': f'https://openstreetmap.org/{osm_type}/{osm_id_right[1:]}',
                'building_text': osm_id_right,
                'building_address': building_address,
                'building_has_ref': pd.notna(df_address['ref:RS:kucni_broj_right'].values[0]),
                'nodes': [],
                'resolution': df_address['resolution'].iloc[0]
            }
            for _, node in df_address.iterrows():
                node_text = node['osm_id_left']
                if pd.notna(node['osm_street_left']) or pd.notna(node['osm_housenumber_left']):
                    node_text = f"{node['osm_street_left'] if pd.notna(node['osm_street_left']) else ''} {node['osm_housenumber_left'] if pd.notna(node['osm_housenumber_left']) else ''}"

                osm_type = 'way' if node['osm_id_left'][0] == 'w' else 'relation' if node['osm_id_left'][0] == 'r' else 'node'
                address['nodes'].append({
                    'link': f"https://openstreetmap.org/{osm_type}/{ node['osm_id_left'][1:]}",
                    'text': node_text,
                    'has_ref': pd.notna(node['ref:RS:kucni_broj_right'])
                })
            addresses.append(address)
            opstina_resolution_stats[resolution] += 1

        output = template.render(
            currentDate=context['dates']['short'],
            reportDate=context['dates']['report'],
            rgzDataDate=context['dates']['rgz_data'],
            osmDataDate=context['dates']['osm_data'],
            addresses=addresses,
            opstina_name=opstina_name,
            resolution_stats=opstina_resolution_stats,
            osm_files_move_address_to_building=osm_files_move_address_to_building
        )

        for resolution, count in opstina_resolution_stats.items():
            resolution_stats[resolution] += count

        with open(opstina_html_path, 'w', encoding='utf-8') as fh:
            fh.write(output)

    if os.path.exists(html_path):
        print("Page data/report/addresses_in_buildings.html already exists")
        return

    print("Generating data/report/addresses_in_buildings.html")

    for i, file in enumerate(sorted(os.listdir(analysis_path))):
        if not file.endswith(".csv"):
            continue
        opstina_name = file[:-4]
        if not any(o for o in opstine if o['name'] == opstina_name):
            opstine.append({
                'name': opstina_name,
                'count': 0
            })
            output = template.render(
                currentDate=context['dates']['short'],
                reportDate=context['dates']['report'],
                rgzDataDate=context['dates']['rgz_data'],
                osmDataDate=context['dates']['osm_data'],
                addresses=[],
                opstina_name=opstina_name,
                resolution_stats={},
                osm_files_move_address_to_building=[],
            )
            opstina_html_path = os.path.join(report_qa_address_path, f'{opstina_name}.html')
            with open(opstina_html_path, 'w', encoding='utf-8') as fh:
                fh.write(output)

    template = env.get_template('qa/addresses_in_buildings.html.tpl')
    output = template.render(
        currentDate=context['dates']['short'],
        reportDate=context['dates']['report'],
        rgzDataDate=context['dates']['rgz_data'],
        osmDataDate=context['dates']['osm_data'],
        opstine=opstine,
        total=total,
        resolution_stats=resolution_stats,
    )

    with open(html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


def generate_unaccounted_osm_qa(context):
    env = context['env']
    cwd = context['cwd']

    qa_path = os.path.join(cwd, 'data/qa')
    analysis_path = os.path.join(cwd, 'data/analysis')
    report_path = os.path.join(cwd, 'data/report')
    html_path = os.path.join(report_path, 'unaccounted_osm_addresses.html')
    report_osm_address_path = os.path.join(report_path, 'osm_addresses')

    template = env.get_template('qa/unaccounted_osm_addresses_opstina.html.tpl')

    if not os.path.exists(report_osm_address_path):
        os.mkdir(report_osm_address_path)

    df_unaccounted_osm_addresses = pd.read_csv(os.path.join(qa_path, 'unaccounted_osm_addresses.csv'))

    opstine = []
    total = {
        'count': 0
    }

    for opstina_name, df_addresses_in_opstina in df_unaccounted_osm_addresses.sort_values('opstina_imel').groupby('opstina_imel'):
        count = len(df_addresses_in_opstina)
        total['count'] += count
        opstine.append({
            'name': opstina_name,
            'count': count
        })
        addresses = []

        opstina_html_path = os.path.join(report_osm_address_path, f'{opstina_name}.html')
        if os.path.exists(opstina_html_path):
            print(f"Page data/report/osm_addresses/{opstina_name}.html already exists")
            continue

        print(f"Generating data/report/osm_addresses/{opstina_name}.html")

        for _, df_address in df_addresses_in_opstina.iterrows():
            address_text = ''
            osm_id = df_address['osm_id']
            street = df_address['osm_street']
            house_number = df_address['osm_housenumber']

            osm_type = 'way' if osm_id[0] == 'w' else 'relation' if osm_id[0] == 'r' else 'node'
            address = {
                'osm_link': f'https://openstreetmap.org/{osm_type}/{osm_id[1:]}',
                'osm_id': osm_id,
                'street': df_address['osm_street'] if pd.notna(df_address['osm_street']) else '',
                'housenumber': df_address['osm_housenumber'] if pd.notna(df_address['osm_housenumber']) else '',
                'name': df_address['name'] if pd.notna(df_address['name']) else '',
                'amenity': df_address['amenity'] if pd.notna(df_address['amenity']) else '',
                'shop': df_address['shop'] if pd.notna(df_address['shop']) else '',
            }
            addresses.append(address)

        output = template.render(
            currentDate=context['dates']['short'],
            reportDate=context['dates']['report'],
            rgzDataDate=context['dates']['rgz_data'],
            osmDataDate=context['dates']['osm_data'],
            addresses=addresses,
            opstina_name=opstina_name
        )

        with open(opstina_html_path, 'w', encoding='utf-8') as fh:
            fh.write(output)

    if os.path.exists(html_path):
        print("Page data/report/unaccounted_osm_addresses.html already exists")
        return

    print("Generating data/report/unaccounted_osm_addresses.html")

    for i, file in enumerate(sorted(os.listdir(analysis_path))):
        if not file.endswith(".csv"):
            continue
        opstina_name = file[:-4]
        if not any(o for o in opstine if o['name'] == opstina_name):
            opstine.append({
                'name': opstina_name,
                'count': 0
            })
            output = template.render(
                currentDate=context['dates']['short'],
                reportDate=context['dates']['report'],
                rgzDataDate=context['dates']['rgz_data'],
                osmDataDate=context['dates']['osm_data'],
                addresses=[],
                opstina_name=opstina_name,
            )
            opstina_html_path = os.path.join(report_osm_address_path, f'{opstina_name}.html')
            with open(opstina_html_path, 'w', encoding='utf-8') as fh:
                fh.write(output)

    template = env.get_template('qa/unaccounted_osm_addresses.html.tpl')
    output = template.render(
        currentDate=context['dates']['short'],
        reportDate=context['dates']['report'],
        rgzDataDate=context['dates']['rgz_data'],
        osmDataDate=context['dates']['osm_data'],
        opstine=opstine,
        total=total,
    )

    with open(html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


def generate_osm_import_qa_rgz_mismatch(context):
    env = context['env']
    cwd = context['cwd']
    street_mappings: StreetMapping = context['street_mappings']

    qa_path = os.path.join(cwd, 'data/qa')
    report_path = os.path.join(cwd, 'data/report')
    osm_import_qa_path = os.path.join(qa_path, 'osm_import_qa.csv')
    html_path = os.path.join(report_path, 'osm_import_qa.html')
    if os.path.exists(html_path):
        print("Page data/report/osm_import_qa.html already exists")
        return

    print("Generating data/report/osm_import_qa.html")

    osm_import_qa_problems = pd.read_csv(osm_import_qa_path)
    osm_import_qa_problems = osm_import_qa_problems[
        pd.isna(osm_import_qa_problems.rgz_kucni_broj_id) |
        ~osm_import_qa_problems.street_perfect_match |
        ~osm_import_qa_problems.housenumber_perfect_match
    ]
    addresses = []

    for _, osm_import_qa_problem in osm_import_qa_problems.iterrows():
        found_in_rgz = pd.notna(osm_import_qa_problem['rgz_kucni_broj_id'])
        rgz_street_match = 1 if osm_import_qa_problem['street_perfect_match'] else 0 if osm_import_qa_problem['street_partial_match'] else -1
        rgz_housenumber_match = 1 if osm_import_qa_problem['housenumber_perfect_match'] else 0 if osm_import_qa_problem['housenumber_partial_match'] else -1
        if found_in_rgz:
            location = osm_import_qa_problem['rgz_geometry'][7:-1].split(' ')
            location_lon = round(float(location[0]), 6)
            location_lat = round(float(location[1]), 6)
            location_url = f'https://www.openstreetmap.org/?mlat={location_lat}&mlon={location_lon}#map=19/{location_lat}/{location_lon}'
        else:
            location_url = None

        if not found_in_rgz:
            priority = 1
        elif rgz_street_match == -1:
            priority = 2
        elif rgz_housenumber_match == -1:
            priority = 3
        elif rgz_street_match == 0:
            priority = 4
        elif rgz_housenumber_match == 0:
            priority = 5
        else:
            priority = 5
        osm_type = 'way' if osm_import_qa_problem['osm_id'][0] == 'w' else 'relation' if osm_import_qa_problem['osm_id'][0] == 'r' else 'node'
        if pd.notna(osm_import_qa_problem['note']) and 'RGZ' in osm_import_qa_problem['note'] and 'Izbrisano iz RGZ-a' not in osm_import_qa_problem['note']:
            note = osm_import_qa_problem['note']
            note_short = note[0:4] + '...' if len(note) > 4 else note
        else:
            note = ''
            note_short = ''

        addresses.append({
            'priority': priority,
            'osm_link': f"https://openstreetmap.org/{osm_type}/{osm_import_qa_problem['osm_id'][1:]}",
            'osm_link_text': osm_import_qa_problem['osm_id'][1:],
            'rgz_link': location_url,
            'osm_street': osm_import_qa_problem['osm_street'],
            'osm_housenumber': osm_import_qa_problem['osm_housenumber'],
            'found_in_rgz': found_in_rgz,
            'rgz_opstina': osm_import_qa_problem['rgz_opstina_lat'],
            'rgz_street': street_mappings.get_name(osm_import_qa_problem['rgz_ulica'], str(osm_import_qa_problem['rgz_ulica_mb'])),
            'rgz_street_match': rgz_street_match,
            'rgz_housenumber': normalize_name_latin(osm_import_qa_problem['rgz_kucni_broj']) if found_in_rgz else '',
            'rgz_housenumber_order': housenumber_to_float(osm_import_qa_problem['rgz_kucni_broj']) if found_in_rgz else 0,
            'rgz_housenumber_match': rgz_housenumber_match,
            'note': note,
            'note_short': note_short
        })
    template = env.get_template('qa/osm_import_qa_rgz_mismatch.html.tpl')
    output = template.render(
        currentDate=context['dates']['short'],
        reportDate=context['dates']['report'],
        rgzDataDate=context['dates']['rgz_data'],
        osmDataDate=context['dates']['osm_data'],
        addresses=addresses
    )
    with open(html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


def generate_osm_import_qa_too_far(context):
    env = context['env']
    cwd = context['cwd']
    street_mappings: StreetMapping = context['street_mappings']

    qa_path = os.path.join(cwd, 'data/qa')
    report_path = os.path.join(cwd, 'data/report')
    osm_import_qa_path = os.path.join(qa_path, 'osm_import_qa.csv')
    html_path = os.path.join(report_path, 'osm_import_qa_too_far.html')
    if os.path.exists(html_path):
        print("Page data/report/osm_import_qa_too_far.html already exists")
        return

    print("Generating data/report/osm_import_qa_too_far.html")

    osm_import_qa_problems = pd.read_csv(osm_import_qa_path)
    osm_import_qa_problems = osm_import_qa_problems[osm_import_qa_problems.distance >= 30]

    addresses = []

    for _, osm_import_qa_problem in osm_import_qa_problems.iterrows():
        location = osm_import_qa_problem['rgz_geometry'][7:-1].split(' ')
        location_lon = round(float(location[0]), 6)
        location_lat = round(float(location[1]), 6)
        location_url = f'https://www.openstreetmap.org/?mlat={location_lat}&mlon={location_lon}#map=19/{location_lat}/{location_lon}'

        osm_type = 'way' if osm_import_qa_problem['osm_id'][0] == 'w' else 'relation' if osm_import_qa_problem['osm_id'][0] == 'r' else 'node'
        if pd.notna(osm_import_qa_problem['note']) and 'RGZ' in osm_import_qa_problem['note'] and 'Izbrisano iz RGZ-a' not in osm_import_qa_problem['note']:
            note = osm_import_qa_problem['note']
            note_short = note[0:4] + '...' if len(note) > 4 else note
        else:
            note = ''
            note_short = ''

        addresses.append({
            'osm_link': f"https://openstreetmap.org/{osm_type}/{osm_import_qa_problem['osm_id'][1:]}",
            'osm_link_text': osm_import_qa_problem['osm_id'][1:],
            'rgz_link': location_url,
            'location_lon': location_lon,
            'location_lat': location_lat,
            'osm_street': osm_import_qa_problem['osm_street'],
            'osm_housenumber': osm_import_qa_problem['osm_housenumber'],
            'rgz_opstina': osm_import_qa_problem['rgz_opstina_lat'],
            'distance': osm_import_qa_problem['distance'],
            'note': note,
            'note_short': note_short
        })
    template = env.get_template('qa/osm_import_qa_too_far.html.tpl')
    output = template.render(
        currentDate=context['dates']['short'],
        reportDate=context['dates']['report'],
        rgzDataDate=context['dates']['rgz_data'],
        osmDataDate=context['dates']['osm_data'],
        addresses=addresses
    )
    with open(html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


def generate_building_addresses_ratio_opstina(context, df_opstina, opstina):
    env = context['env']
    cwd = context['cwd']

    stats_report_path = os.path.join(cwd, 'data/report/b-hn')
    html_path = os.path.join(stats_report_path, f'{opstina}.html')
    if os.path.exists(html_path):
        print(f"Page data/report/b-hn/{opstina}.html already exists")
        return

    naselja = []
    for _, df_naselje in df_opstina.iterrows():
        building_count = df_naselje['building_count']
        addresses_count = df_naselje['addresses_count']
        if addresses_count > 0:
            ratio_str = 100 * building_count / addresses_count
            ratio = f'{ratio_str:.2f} %'
            ratio_order = 100 * building_count / addresses_count
            if ratio_order > 100000:
                ratio_order = 100000
        else:
            ratio = '+∞ %'
            ratio_order = 100001

        naselja.append({
            'naselje': df_naselje['naselje_imel'],
            'building_count': building_count,
            'addresses_count': addresses_count,
            'ratio': ratio,
            'ratio_order': ratio_order
        })

    print(f"Generating data/report/b-hn/{opstina}.html")
    template = env.get_template('qa/b_hn_stats_opstina.html.tpl')
    output = template.render(
        currentDate=context['dates']['short'],
        reportDate=context['dates']['report'],
        rgzDataDate=context['dates']['rgz_data'],
        osmDataDate=context['dates']['osm_data'],
        opstina=opstina,
        naselja=naselja
    )

    with open(html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


def generate_building_addresses_ratio(context):
    env = context['env']
    cwd = context['cwd']
    data_path = context['data_path']
    bhn_path = os.path.join(data_path, 'b-hn')

    df_naselja = pd.read_csv(os.path.join(bhn_path, 'building_housenumber_per_naselje.csv'))
    for opstina in df_naselja.opstina_imel.unique():
        generate_building_addresses_ratio_opstina(context, df_naselja[df_naselja.opstina_imel == opstina], opstina)

    # Generate index.html
    stats_report_path = os.path.join(cwd, 'data/report/b-hn')
    html_path = os.path.join(stats_report_path, 'index.html')
    if os.path.exists(html_path):
        print("Page data/report/b-hn/index.html already exists")
        return

    opstine = []
    for opstina, df_opstina in df_naselja.groupby('opstina_imel').agg({'building_count': 'sum', 'addresses_count': 'sum'}).iterrows():
        building_count = df_opstina['building_count']
        addresses_count = df_opstina['addresses_count']
        if addresses_count > 0:
            ratio_str = 100 * building_count / addresses_count
            ratio = f'{ratio_str:.2f} %'
            ratio_order = 100 * building_count / addresses_count
            if ratio_order > 100000:
                ratio_order = 100000
        else:
            ratio = '+∞ %'
            ratio_order = 100001

        opstine.append({
            'opstina': opstina,
            'building_count': building_count,
            'addresses_count': addresses_count,
            'ratio': ratio,
            'ratio_order': ratio_order
        })

    print("Generating data/report/b-hn/index.html")
    template = env.get_template('qa/b_hn_stats.html.tpl')
    output = template.render(
        currentDate=context['dates']['short'],
        reportDate=context['dates']['report'],
        rgzDataDate=context['dates']['rgz_data'],
        osmDataDate=context['dates']['osm_data'],
        opstine=opstine
    )
    with open(html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


def generate_removed_addresses(context):
    env = context['env']
    cwd = context['cwd']

    qa_path = os.path.join(cwd, 'data/qa')
    analysis_path = os.path.join(cwd, 'data/analysis')
    report_path = os.path.join(cwd, 'data/report')
    html_path = os.path.join(report_path, 'removed_addresses.html')
    report_removed_address_path = os.path.join(report_path, 'removed_addresses')

    template = env.get_template('qa/removed_addresses_opstina.html.tpl')

    if not os.path.exists(report_removed_address_path):
        os.mkdir(report_removed_address_path)

    df_removed_osm_addresses = pd.read_csv(os.path.join(qa_path, 'removed_addresses.csv'))

    opstine = []
    total = {
        'count': 0
    }

    for opstina_name, df_addresses_in_opstina in df_removed_osm_addresses.sort_values('opstina_imel').groupby('opstina_imel'):
        count = len(df_addresses_in_opstina)
        total['count'] += count
        opstine.append({
            'name': opstina_name,
            'count': count
        })
        addresses = []

        opstina_html_path = os.path.join(report_removed_address_path, f'{opstina_name}.html')
        if os.path.exists(opstina_html_path):
            print(f"Page data/report/removed_addresses/{opstina_name}.html already exists")
            continue

        print(f"Generating data/report/removed_addresses/{opstina_name}.html")

        for _, df_address in df_addresses_in_opstina.iterrows():
            address_text = ''
            osm_id = df_address['osm_id']
            street = df_address['osm_street']
            house_number = df_address['osm_housenumber']

            osm_type = 'way' if osm_id[0] == 'w' else 'relation' if osm_id[0] == 'r' else 'node'
            address = {
                'osm_link': f'https://openstreetmap.org/{osm_type}/{osm_id[1:]}',
                'osm_id': osm_id,
                'street': df_address['osm_street'] if pd.notna(df_address['osm_street']) else '',
                'housenumber': df_address['osm_housenumber'] if pd.notna(df_address['osm_housenumber']) else '',
                'removal_date': df_address['removal_date'] if pd.notna(df_address['removal_date']) else '',
                'rgz_id': df_address['removed:ref:RS:kucni_broj'] if pd.notna(df_address['removed:ref:RS:kucni_broj']) else '',
            }
            addresses.append(address)

        output = template.render(
            currentDate=context['dates']['short'],
            reportDate=context['dates']['report'],
            rgzDataDate=context['dates']['rgz_data'],
            osmDataDate=context['dates']['osm_data'],
            addresses=addresses,
            opstina_name=opstina_name
        )

        with open(opstina_html_path, 'w', encoding='utf-8') as fh:
            fh.write(output)

    if os.path.exists(html_path):
        print("Page data/report/removed_addresses.html already exists")
        return

    print("Generating data/report/removed_addresses.html")

    for i, file in enumerate(sorted(os.listdir(analysis_path))):
        if not file.endswith(".csv"):
            continue
        opstina_name = file[:-4]
        if not any(o for o in opstine if o['name'] == opstina_name):
            opstine.append({
                'name': opstina_name,
                'count': 0
            })
            output = template.render(
                currentDate=context['dates']['short'],
                reportDate=context['dates']['report'],
                rgzDataDate=context['dates']['rgz_data'],
                osmDataDate=context['dates']['osm_data'],
                addresses=[],
                opstina_name=opstina_name,
            )
            opstina_html_path = os.path.join(report_removed_address_path, f'{opstina_name}.html')
            with open(opstina_html_path, 'w', encoding='utf-8') as fh:
                fh.write(output)

    template = env.get_template('qa/removed_addresses.html.tpl')
    output = template.render(
        reportDate=context['dates']['report'],
        rgzDataDate=context['dates']['rgz_data'],
        osmDataDate=context['dates']['osm_data'],
        currentDate=context['dates']['short'],
        opstine=opstine,
        total=total,
    )

    with open(html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


def generate_street_mapping(context):
    env = context['env']
    cwd = context['cwd']

    report_path = os.path.join(cwd, 'data/report')
    html_path = os.path.join(report_path, 'street_mapping.html')

    if os.path.exists(html_path):
        print("Page data/report/street_mapping.html already exists")
        return

    print("Generating data/report/street_mapping.html")

    street_mappings: StreetMapping = context['street_mappings']
    all_rgz_names = street_mappings.get_all_rgz_names()

    letter_values = {
        'А': 1, 'Б': 2, 'В': 3, 'Г': 4, 'Д': 5, 'Ђ': 6, 'Е': 7, 'Ж': 8, 'З': 9, 'И': 10,
        'Ј': 11, 'К': 12, 'Л': 13, 'Љ': 14, 'М': 15, 'Н': 16, 'Њ': 17, 'О': 18, 'П': 19, 'Р': 20,
        'С': 21, 'Т': 22, 'Ћ': 23, 'У': 24, 'Ф': 25, 'Х': 26, 'Ц': 27, 'Ч': 28, 'Џ': 29, 'Ш': 30,
    }

    rgz_names_sorted = sorted(all_rgz_names, key=lambda x: [(1000+letter_values[c]) if c in letter_values else ord(c) for c in x.upper()])
    street_names = []
    for rgz_name in rgz_names_sorted:
        names = street_mappings.get_all_names_for_rgz_name(rgz_name)
        default_name = next(n for n in names if n['ulica_id'] == '')
        osm_name = default_name['name']
        default_source = default_name['source']
        default_refs = default_name['refs']
        refs = []
        for osm_id in default_refs.split(','):
            if len(osm_id) < 2:
                continue
            osm_type = 'way' if osm_id[0] == 'w' else 'relation' if osm_id[0] == 'r' else 'node'
            osm_link = f'https://openstreetmap.org/{osm_type}/{osm_id[1:]}'
            refs.append({'osm_id': osm_id, 'osm_link': osm_link})
        refs_count = len(refs)
        refs = refs[0:5]
        exceptions = [n for n in names if n['ulica_id'] != '']
        rgz_name_html = rgz_name
        if rgz_name_html.startswith(' '):
            rgz_name_html = '␣' + rgz_name_html[1:]
        if rgz_name_html.endswith(' '):
            rgz_name_html = rgz_name_html[:-1] + '␣'
        street_names.append({
            'rgz_name': rgz_name_html,
            'name': osm_name,
            'source': default_source,
            'refs': refs,
            'refs_count': refs_count,
            'exceptions': exceptions
        })

    template = env.get_template('qa/street_mapping_qa.html.tpl')
    output = template.render(
        reportDate=context['dates']['report'],
        rgzDataDate=context['dates']['rgz_data'],
        osmDataDate=context['dates']['osm_data'],
        currentDate=context['dates']['short'],
        street_names=street_names,
    )

    with open(html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


def generate_qa(context):
    env = context['env']
    cwd = context['cwd']

    print("Generating QA pages")

    generate_osm_import_qa_rgz_mismatch(context)
    generate_osm_import_qa_too_far(context)
    generate_qa_duplicated_refs(context)
    generate_addresses_in_buildings(context)
    generate_unaccounted_osm_qa(context)
    generate_building_addresses_ratio(context)
    generate_removed_addresses(context)
    generate_street_mapping(context)

    report_path = os.path.join(cwd, 'data/report')
    html_path = os.path.join(report_path, 'qa.html')
    if os.path.exists(html_path):
        print("Page data/report/qa.html already exists")
        return

    print("Generating data/report/qa.html")
    template = env.get_template('qa.html')
    output = template.render(
        currentDate=context['dates']['short'],
        reportDate=context['dates']['report'],
        rgzDataDate=context['dates']['rgz_data'],
        osmDataDate=context['dates']['osm_data']
    )
    with open(html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


def main():
    # TODO: address should be searchable with latin only
    env = Environment(loader=FileSystemLoader(searchpath='./templates'))
    env.globals.update(len=len, AddressInBuildingResolution=AddressInBuildingResolution)
    cwd = os.getcwd()

    data_path = os.path.join(cwd, 'data')
    rgz_path = os.path.join(data_path, 'rgz')

    print("Building cache of OSM entities")
    osm_entities_cache = build_osm_entities_cache(data_path)

    print("Loading normalized street names mapping")
    street_mappings = StreetMapping(cwd)

    running_file = os.path.join(data_path, 'running')
    if not os.path.exists(running_file):
       raise Exception("File data/running missing, no way to determine date when OSM data was retrieved")
    with open(running_file, 'r') as file:
       file_content = file.read().rstrip()
       osm_data_timestamp = datetime.datetime.fromisoformat(file_content).strftime('%d.%m.%Y. %H:%M')

    rgz_date_file = os.path.join(rgz_path, 'LATEST')
    if not os.path.exists(rgz_date_file):
        raise Exception("File data/rgz/LATEST missing, no way to determine date when RGZ data was retrived")
    with open(rgz_date_file, 'r') as file:
        file_content = file.read().rstrip()
        rgz_data_timestamp = datetime.datetime.fromisoformat(file_content).strftime('%d.%m.%Y.')

    context = {
        'env': env,
        'cwd': cwd,
        'data_path': data_path,
        'dates': {
            'short': datetime.date.today().strftime('%Y-%m-%d'),
            'report': datetime.datetime.now().strftime('%d.%m.%Y. %H:%M'),
            'osm_data': osm_data_timestamp,
            'rgz_data': rgz_data_timestamp,
        },
        'osm_entities_cache': osm_entities_cache,
        'street_mappings': street_mappings
    }

    generate_qa(context)


if __name__ == '__main__':
    main()
