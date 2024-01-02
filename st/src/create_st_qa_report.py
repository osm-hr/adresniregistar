# -*- coding: utf-8 -*-

import datetime
import os

import geopandas as gpd
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from shapely import wkt

from common import cyr2lat_small
from street_mapping import StreetMapping


def generate_wrong_names_report(context):
    env = context['env']
    cwd = context['cwd']
    street_mappings = context['street_mappings']

    qa_path = os.path.join(cwd, 'data/qa')
    analysis_path = os.path.join(cwd, 'data/analysis')
    report_path = os.path.join(cwd, 'data/report')
    html_path = os.path.join(report_path, 'wrong_names.html')
    wrong_names_osm_address_path = os.path.join(report_path, 'wrong_names')

    template = env.get_template('qa/wrong_names_opstina.html.tpl')

    if not os.path.exists(wrong_names_osm_address_path):
        os.mkdir(wrong_names_osm_address_path)

    df_wrong_street_names = pd.read_csv(os.path.join(qa_path, 'wrong_street_names.csv'))

    opstine = []
    total = {
        'wrong_name': 0,
        'missing_name': 0,
        'wrong_name_sr': 0,
        'missing_name_sr': 0,
        'wrong_name_sr_latn': 0,
        'missing_name_sr_latn': 0
    }

    for opstina_name, df_wrong_street_names_in_opstina in df_wrong_street_names.sort_values('opstina_imel').groupby('opstina_imel'):
        wrong_name_count = len(df_wrong_street_names_in_opstina[df_wrong_street_names_in_opstina.wrong_name])
        missing_name_count = len(df_wrong_street_names_in_opstina[df_wrong_street_names_in_opstina.missing_name])
        wrong_name_sr_count = len(df_wrong_street_names_in_opstina[df_wrong_street_names_in_opstina.wrong_name_sr])
        missing_name_sr_count = len(df_wrong_street_names_in_opstina[df_wrong_street_names_in_opstina.missing_name_sr])
        wrong_name_sr_latn_count = len(df_wrong_street_names_in_opstina[df_wrong_street_names_in_opstina.wrong_name_sr_latn])
        missing_name_sr_latn_count = len(df_wrong_street_names_in_opstina[df_wrong_street_names_in_opstina.missing_name_sr_latn])

        total['wrong_name'] += wrong_name_count
        total['missing_name'] += missing_name_count
        total['wrong_name_sr'] += wrong_name_sr_count
        total['missing_name_sr'] += missing_name_sr_count
        total['wrong_name_sr_latn'] += wrong_name_sr_latn_count
        total['missing_name_sr_latn'] += missing_name_sr_latn_count
        opstine.append({
            'name': opstina_name,
            'wrong_name': wrong_name_count,
            'missing_name': missing_name_count,
            'wrong_name_sr': wrong_name_sr_count,
            'missing_name_sr': missing_name_sr_count,
            'wrong_name_sr_latn': wrong_name_sr_latn_count,
            'missing_name_sr_latn': missing_name_sr_latn_count
        })
        streets = []

        opstina_html_path = os.path.join(wrong_names_osm_address_path, f'{opstina_name}.html')
        if os.path.exists(opstina_html_path):
            print(f"Page data/report/wrong_names/{opstina_name}.html already exists")
            continue

        print(f"Generating data/report/wrong_names/{opstina_name}.html")

        for _, df_street in df_wrong_street_names_in_opstina.iterrows():
            osm_id = df_street['osm_id']
            osm_type = 'way' if osm_id[0] == 'w' else 'relation' if osm_id[0] == 'r' else 'node'
            if pd.notna(df_street['rgz_ulica_proper']) and df_street['rgz_ulica_proper'] != '':
                osm_name_sr_proper = df_street['rgz_ulica_proper']
                osm_name_sr_latn_proper = cyr2lat_small(osm_name_sr_proper)
            else:
                if pd.notna(df_street['osm_name']):
                    osm_name_sr_proper = df_street['osm_name']
                    osm_name_sr_latn_proper = cyr2lat_small(osm_name_sr_proper)
                else:
                    osm_name_sr_proper = '?'
                    osm_name_sr_latn_proper = '?'

            street = {
                'osm_link': f'https://openstreetmap.org/{osm_type}/{osm_id[1:]}',
                'osm_id': osm_id,
                'has_ref_rs_ulica': True if pd.notna(df_street['ref:RS:ulica']) and df_street['ref:RS:ulica'] else False,
                'osm_name': df_street['osm_name'] if pd.notna(df_street['osm_name']) else '',
                'osm_name_proper': df_street['rgz_ulica_proper'] if pd.notna(df_street['rgz_ulica_proper']) else '',
                'osm_name_sr': df_street['osm_name_sr'] if pd.notna(df_street['osm_name_sr']) else '',
                'osm_name_sr_proper': osm_name_sr_proper,
                'osm_name_sr_latn': df_street['osm_name_sr_latn'] if pd.notna(df_street['osm_name_sr_latn']) else '',
                'osm_name_sr_latn_proper': osm_name_sr_latn_proper,
                'wrong_name': df_street['wrong_name'],
                'missing_name': df_street['missing_name'],
                'wrong_name_sr': df_street['wrong_name_sr'],
                'missing_name_sr': df_street['missing_name_sr'],
                'wrong_name_sr_latn': df_street['wrong_name_sr_latn'],
                'missing_name_sr_latn': df_street['missing_name_sr_latn'],
            }
            streets.append(street)

        output = template.render(
            currentDate=context['dates']['short'],
            reportDate=context['dates']['report'],
            osmDataDate=context['dates']['osm_data'],
            rgzDataDate=context['dates']['rgz_data'],
            streets=streets,
            opstina_name=opstina_name
        )

        with open(opstina_html_path, 'w', encoding='utf-8') as fh:
            fh.write(output)

    if os.path.exists(html_path):
        print("Page data/report/wrong_names.html already exists")
        return

    print("Generating data/report/wrong_names.html")

    for i, file in enumerate(sorted(os.listdir(analysis_path))):
        if not file.endswith(".csv"):
            continue
        opstina_name = file[:-4]
        if not any(o for o in opstine if o['name'] == opstina_name):
            opstine.append({
                'name': opstina_name,
                'wrong_name': 0,
                'missing_name': 0,
                'wrong_name_sr': 0,
                'missing_name_sr': 0,
                'wrong_name_sr_latn': 0,
                'missing_name_sr_latn': 0
            })
            output = template.render(
                currentDate=context['dates']['short'],
                reportDate=context['dates']['report'],
                osmDataDate=context['dates']['osm_data'],
                rgzDataDate=context['dates']['rgz_data'],
                streets=[],
                opstina_name=opstina_name,
            )
            opstina_html_path = os.path.join(wrong_names_osm_address_path, f'{opstina_name}.html')
            with open(opstina_html_path, 'w', encoding='utf-8') as fh:
                fh.write(output)

    template = env.get_template('qa/wrong_names.html.tpl')
    output = template.render(
        currentDate=context['dates']['short'],
        reportDate=context['dates']['report'],
        osmDataDate=context['dates']['osm_data'],
        rgzDataDate=context['dates']['rgz_data'],
        opstine=opstine,
        total=total,
    )

    with open(html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


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
    cwd = os.getcwd()

    data_path = os.path.join(cwd, 'data')
    rgz_path = os.path.join(data_path, 'rgz')

    running_file = os.path.join(data_path, 'running')
    if not os.path.exists(running_file):
        raise Exception("File data/running missing, no way to determine date when OSM data was retrived")
    with open(running_file, 'r') as file:
        file_content = file.read().rstrip()
        osm_data_timestamp = datetime.datetime.fromisoformat(file_content).strftime('%d.%m.%Y. %H:%M')

    rgz_date_file = os.path.join(rgz_path, 'LATEST')
    if not os.path.exists(rgz_date_file):
        raise Exception("File data/rgz/LATEST missing, no way to determine date when RGZ data was retrived")
    with open(rgz_date_file, 'r') as file:
        file_content = file.read().rstrip()
        rgz_data_timestamp = datetime.datetime.fromisoformat(file_content).strftime('%d.%m.%Y.')

    print("Loading normalized street names mapping")
    street_mappings = StreetMapping(os.path.join(cwd, '..', 'ar'))

    print("Loading boundaries of naselja")
    gdf_naselja = None #load_naselja_boundaries(rgz_path)

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
        'street_mappings': street_mappings,
        'gdf_naselja': gdf_naselja
    }
    generate_wrong_names_report(context)

    report_path = os.path.join(cwd, 'data/report')
    qa_html_path = os.path.join(report_path, 'qa.html')
    if os.path.exists(qa_html_path):
        print(f"Page {os.path.relpath(qa_html_path)} already exists")
        return

    print(f"Generating {os.path.relpath(qa_html_path)}")
    template = env.get_template('qa.html.tpl')
    output = template.render(
        currentDate=context['dates']['short'],
        reportDate=context['dates']['report'],
        osmDataDate=context['dates']['osm_data'],
        rgzDataDate=context['dates']['rgz_data'],
    )
    with open(qa_html_path, 'w', encoding='utf-8') as fh:
        fh.write(output)


if __name__ == '__main__':
    main()
