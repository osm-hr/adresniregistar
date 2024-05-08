# -*- coding: utf-8 -*-

import datetime
import json
import os

import numpy as np
import pandas as pd
from jinja2 import Environment, FileSystemLoader

from common import cyr2lat, ApartmentResolution


def generate_report(context):
    env = context['env']
    cwd = context['cwd']
    data_path = os.path.join(cwd, 'data/')
    report_path = os.path.join(cwd, 'output/')
    template = env.get_template('index-opstina.html.tpl')

    df_data = pd.read_csv(os.path.join(data_path, 'sz_analysis.csv'))
    df_data['resolution'] = df_data['resolution'].apply(lambda x: ApartmentResolution(x) if pd.notna(x) else np.nan)

    opstine = []
    total = {
        'sz_count': 0,
        'found_in_rgz': 0,
        'found_in_osm': 0,
        'apartments_count': 0
    }
    for opstina_name, df_sz_in_opstina in df_data.sort_values('sz_opstina').groupby('sz_opstina'):
        opstina_name = cyr2lat(opstina_name)
        sz_count = len(df_sz_in_opstina)
        found_in_rgz_count = len(df_sz_in_opstina[df_sz_in_opstina.found_in_rgz])
        found_in_osm_count = len(df_sz_in_opstina[df_sz_in_opstina.found_in_osm])
        apartments_count = len(df_sz_in_opstina[df_sz_in_opstina.resolution == ApartmentResolution.OSM_ENTITY_APARTMENT])
        total['sz_count'] += sz_count
        total['found_in_rgz'] += found_in_rgz_count
        total['found_in_osm'] += found_in_osm_count
        total['apartments_count'] += apartments_count

        opstine.append({
            'name': opstina_name,
            'sz_count': sz_count,
            'found_in_rgz': found_in_rgz_count,
            'found_in_osm': found_in_osm_count,
            'apartments_count': apartments_count
        })
        addresses = []

        opstina_html_path = os.path.join(report_path, f'{opstina_name}.html')
        if os.path.exists(opstina_html_path):
            print(f"Page output/{opstina_name}.html already exists")
            #continue

        print(f"Generating output/{opstina_name}.html")

        for _, df_address in df_sz_in_opstina.iterrows():
            found_in_rgz = df_address['found_in_rgz']
            found_in_osm = df_address['found_in_osm']

            if found_in_rgz:
                rgz_loc = df_address['rgz_geometry'][7:-1].split(' ')
                rgz_loc_lon = round(float(rgz_loc[0]), 6)
                rgz_loc_lat = round(float(rgz_loc[1]), 6)
                rgz_link = f'https://www.openstreetmap.org/?mlat={rgz_loc_lat}&mlon={rgz_loc_lon}#map=19/{rgz_loc_lat}/{rgz_loc_lon}'
            else:
                rgz_link = None

            if found_in_osm:
                osm_links = []
                for osm_id in json.loads(df_address['osm_id']):
                    osm_type = 'way' if osm_id[0] == 'w' else 'relation' if osm_id[0] == 'r' else 'node'
                    osm_link = f"https://openstreetmap.org/{osm_type}/{osm_id[1:]}"
                    osm_links.append(osm_link)
            else:
                osm_links = None

            address = {
                'sz_ime': df_address['sz_ime'],
                'sz_ulica': df_address['sz_ulica'],
                'sz_kucni_broj': df_address['sz_kucni_broj'],
                'found_in_rgz': found_in_rgz,
                'rgz_kucni_broj_id': int(df_address['rgz_kucni_broj_id']) if pd.notna(df_address['rgz_kucni_broj_id']) else 0,
                'rgz_ulica': df_address['rgz_ulica'],
                'rgz_kucni_broj': df_address['rgz_kucni_broj'],
                'rgz_link': rgz_link,
                'is_duplicated': df_address['is_duplicated'],
                'duplicated_naselja': df_address['duplicated_naselja'] if pd.notna(df_address['duplicated_naselja']) else None,
                'found_in_osm': found_in_osm,
                'osm_streets': json.loads(df_address['osm_street']) if pd.notna(df_address['osm_street']) else None,
                'osm_housenumbers': json.loads(df_address['osm_housenumber']) if pd.notna(df_address['osm_housenumber']) else None,
                'osm_links': osm_links,
                'resolution': df_address['resolution']
            }
            addresses.append(address)

        total_opstina = {
            'sz_count': sz_count,
            'found_in_rgz': found_in_rgz_count,
            'found_in_osm': found_in_osm_count,
            'apartments_count': apartments_count
        }

        osm_breakdown = {}
        for r in ApartmentResolution:
            osm_breakdown[r] = len(df_sz_in_opstina[df_sz_in_opstina['resolution'] == r])

        output = template.render(
            currentDate=context['dates']['short'],
            reportDate=context['dates']['report'],
            osmDataDate=context['dates']['osm_data'],
            rgzDataDate=context['dates']['rgz_data'],
            addresses=addresses,
            opstina_name=opstina_name,
            total=total_opstina,
            osm_breakdown=osm_breakdown
        )

        with open(opstina_html_path, 'w', encoding='utf-8') as fh:
            fh.write(output)

    print("Generating output/index.html")
    html_path = os.path.join(report_path, 'index.html')
    if os.path.exists(html_path):
        print("Page output/index.html already exists")
        #return

    template = env.get_template('index.html.tpl')
    output = template.render(
        currentDate=context['dates']['short'],
        reportDate=context['dates']['report'],
        rgzDataDate=context['dates']['rgz_data'],
        osmDataDate=context['dates']['osm_data'],
        opstine=opstine,
        total=total
    )

    with open(html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


def main():
    env = Environment(loader=FileSystemLoader(searchpath='./templates'))
    env.globals.update(len=len, ApartmentResolution=ApartmentResolution)
    cwd = os.getcwd()

    rgz_date_file = os.path.join(cwd, 'data/LATEST')
    if not os.path.exists(rgz_date_file):
        raise Exception("File data/LATEST missing, no way to determine date when RGZ data was retrived")
    with open(rgz_date_file, 'r') as file:
        file_content = file.read().rstrip()
        rgz_data_timestamp = datetime.datetime.fromisoformat(file_content).strftime('%d.%m.%Y.')

    context = {
        'env': env,
        'cwd': cwd,
        'dates': {
            'short': datetime.date.today().strftime('%Y-%m-%d'),
            'report': datetime.datetime.now().strftime('%d.%m.%Y. %H:%M'),
            'osm_data': datetime.datetime.now().strftime('%d.%m.%Y. %H:%M'),
            'rgz_data': rgz_data_timestamp,
        }
    }
    generate_report(context)


if __name__ == '__main__':
    main()
