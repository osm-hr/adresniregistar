# -*- coding: utf-8 -*-

from common import cyr2lat

import os
import sys
from jinja2 import Environment, PackageLoader, FileSystemLoader
import csv
import datetime
import pandas as pd

csv.field_size_limit(sys.maxsize)


def generate_naselje(env, opstina_dir_path, opstina_name, naselje, df_naselje):
    template = env.get_template('naselje.html')
    current_date = datetime.date.today().strftime('%Y-%m-%d')
    current_date_srb = datetime.date.today().strftime('%d.%m.%Y')
    naselje_dir_path = os.path.join(opstina_dir_path, opstina_name)
    if not os.path.exists(naselje_dir_path):
        os.mkdir(naselje_dir_path)
    naselje_path = os.path.join(naselje_dir_path, f'{naselje["name_lat"]}.html')

    addresses = []
    for _, address in df_naselje.iterrows():
        location = address['rgz_geometry'][7:-1].split(' ')
        location_lon = round(float(location[0]), 6)
        location_lat = round(float(location[1]), 6)
        location_url = f'https://www.openstreetmap.org/?mlat={location_lat}&mlon={location_lon}#map=19/{location_lat}/{location_lon}'
        location_text = f'{location_lat}, {location_lon}'
        osm_link, osm_street, osm_housenumber, score, distance = '', '', '', '', ''
        if type(address['osm_id']) == str:
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
            'conflated': '✅' if address['conflated'] else '❌',
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
        opstina_name=opstina_name)
    with open(naselje_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


def generate_opstina(env, report_path, opstina_name, df_opstina):
    template = env.get_template('opstina.html')
    current_date = datetime.date.today().strftime('%Y-%m-%d')
    current_date_srb = datetime.date.today().strftime('%d.%m.%Y')
    opstine_dir_path = os.path.join(report_path, 'opstine')
    if not os.path.exists(opstine_dir_path):
        os.mkdir(opstine_dir_path)

    rgz_count = len(df_opstina)
    matched_count = len(df_opstina[df_opstina['matching'] == True])
    opstina = {
        'name': opstina_name,
        'rgz': rgz_count,
        'osm': 'N/A',
        'conflated': 0,
        'matched': matched_count
    }

    naselja = []

    for naselje_name, df_naselje in df_opstina.groupby('rgz_naselje'):  # .agg({'rgz_kucni_broj_id': 'count'}).iterrows():
        # df_naselje = df_opstina[df_opstina['rgz_naselje'] == naselje_name]
        rgz_count = len(df_naselje)
        matched_count = df_naselje[df_naselje['matching'] == True]
        naselje = {
            'name': naselje_name,
            'name_lat': cyr2lat(naselje_name),
            'rgz': rgz_count,
            'osm': 'N/A',
            'conflated': 0,
            'matched': len(matched_count)
        }
        generate_naselje(env, opstine_dir_path, opstina_name, naselje, df_naselje)

        naselja.append(naselje)

    output = template.render(
        currentDate=current_date,
        currentDateSrb=current_date_srb,
        naselja=naselja,
        opstina=opstina)
    with open(os.path.join(opstine_dir_path, f'{opstina_name}.html'), 'w', encoding='utf-8') as fh:
        fh.write(output)
    return opstina


def generate_index(env):
    template = env.get_template('index.html')

    cwd = os.getcwd()
    analysis_path = os.path.join(cwd, 'data/analysis')
    report_path = os.path.join(cwd, 'data/report')
    total_csvs = len(os.listdir(analysis_path))

    total = {
        'rgz': 0,
        'osm': 0,
        'conflated': 0,
        'matched': 0
    }
    opstine = []
    for i, file in enumerate(os.listdir(analysis_path)):
        if not file.endswith(".csv"):
            continue
        opstina_name = file[:-4]
        print(f"{i+1}/{total_csvs} Processing {opstina_name}")
        df_opstina = pd.read_csv(os.path.join(analysis_path, file))
        opstina = generate_opstina(env, report_path, opstina_name, df_opstina)
        opstine.append(opstina)
        total['rgz'] += opstina['rgz']
        total['matched'] += opstina['matched']

    current_date = datetime.date.today().strftime('%Y-%m-%d')
    current_date_srb = datetime.date.today().strftime('%d.%m.%Y')
    output = template.render(
        currentDate=current_date,
        currentDateSrb=current_date_srb,
        opstine=opstine,
        total=total)
    with open(os.path.join(report_path, 'index.html'), 'w', encoding='utf-8') as fh:
        fh.write(output)


def main():
    env = Environment(loader=FileSystemLoader(searchpath='./templates'))
    generate_index(env)


if __name__ == '__main__':
    main()