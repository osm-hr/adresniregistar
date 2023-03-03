# -*- coding: utf-8 -*-

from common import cyr2lat

import os
import sys
from jinja2 import Environment, PackageLoader, FileSystemLoader
import csv
from common import normalize_name_latin
import datetime
import pandas as pd


street_mappings = {}


def load_mappings(data_path):
    global street_mappings
    with open(os.path.join(data_path, 'mapping', 'mapping.csv'), encoding='utf-8') as mapping_csv_file:
        reader = csv.DictReader(mapping_csv_file)
        for row in reader:
            street_mappings[row['rgz_name']] = row['name']


def generate_osm_files(env, opstina_dir_path, opstina_name, naselje, df_naselje):
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
            filename = f'{naselje["name_lat"]}-{counter}.osm'
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
    old_counter = counter
    counter = counter + len(osm_entities)
    output = template.render(osm_entities=osm_entities)
    filename = f'{naselje["name_lat"]}-{counter}.osm'
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


def generate_naselje(env, opstina_dir_path, opstina_name, naselje, df_naselje):
    template = env.get_template('naselje.html')
    current_date = datetime.date.today().strftime('%Y-%m-%d')
    current_date_srb = datetime.date.today().strftime('%d.%m.%Y')
    naselje_dir_path = os.path.join(opstina_dir_path, opstina_name)
    if not os.path.exists(naselje_dir_path):
        os.mkdir(naselje_dir_path)

    osm_files = generate_osm_files(env, opstina_dir_path, opstina_name, naselje, df_naselje)

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
            osm_type = 'node' if address['conflated_osm_id'][0] == 'n' else 'way' if address['osm_id'][0] == 'w' else 'relation'
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
        osm_files=osm_files)
    with open(naselje_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


def generate_opstina(env, report_path, opstina_name, df_opstina, df_opstina_osm):
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
        generate_naselje(env, opstine_dir_path, opstina_name, naselje, df_naselje)

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


def generate_index(env):
    template = env.get_template('index.html')

    cwd = os.getcwd()
    data_path = os.path.join(cwd, 'data')
    load_mappings(data_path)
    osm_path = os.path.join(data_path, 'osm', 'csv')
    analysis_path = os.path.join(data_path, 'analysis')
    report_path = os.path.join(data_path, 'report')
    total_csvs = len(os.listdir(analysis_path))
    index_html_path = os.path.join(report_path, 'index.html')

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
        opstina = generate_opstina(env, report_path, opstina_name, df_opstina, df_opstina_osm)
        opstine.append(opstina)
        total['conflated'] += opstina['conflated']
        total['rgz'] += opstina['rgz']
        total['osm'] += opstina['osm']
        total['matched'] += opstina['matched']
        total['partially_matched_count'] += opstina['partially_matched_count']
        print()

    if os.path.exists(index_html_path):
        return

    current_date = datetime.date.today().strftime('%Y-%m-%d')
    current_date_srb = datetime.date.today().strftime('%d.%m.%Y')
    output = template.render(
        currentDate=current_date,
        currentDateSrb=current_date_srb,
        opstine=opstine,
        total=total)
    with open(index_html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


def main():
    # TODO: sorting in some columns should be as numbers (distance, kucni broj)
    # TODO: address should be searchable with latin only
    env = Environment(loader=FileSystemLoader(searchpath='./templates'))
    env.globals.update(len=len)
    generate_index(env)


if __name__ == '__main__':
    main()
