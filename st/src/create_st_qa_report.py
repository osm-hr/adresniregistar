# -*- coding: utf-8 -*-

import datetime
import os

import geopandas as gpd
import numpy as np
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from shapely import wkt

from common import cyr2lat_small, cyr2intname
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

    df_wrong_street_names = pd.read_csv(os.path.join(qa_path, 'wrong_street_names.csv'), dtype={'ref:RS:ulica': 'string'})

    opstine = []
    total = {
        'wrong_name': 0,
        'missing_name': 0,
        'wrong_name_sr': 0,
        'missing_name_sr': 0,
        'wrong_name_sr_latn': 0,
        'missing_name_sr_latn': 0
    }
    df_wrong_street_names = df_wrong_street_names[
        df_wrong_street_names.wrong_name |
        df_wrong_street_names.missing_name |
        df_wrong_street_names.wrong_name_sr |
        df_wrong_street_names.missing_name_sr |
        df_wrong_street_names.wrong_name_sr_latn |
        df_wrong_street_names.missing_name_sr_latn
    ]

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


def generate_english_names_report(context):
    env = context['env']
    cwd = context['cwd']

    qa_path = os.path.join(cwd, 'data/qa')
    analysis_path = os.path.join(cwd, 'data/analysis')
    report_path = os.path.join(cwd, 'data/report')
    html_path = os.path.join(report_path, 'en_names.html')
    en_names_osm_address_path = os.path.join(report_path, 'en_names')

    template = env.get_template('qa/en_names_opstina.html.tpl')

    if not os.path.exists(en_names_osm_address_path):
        os.mkdir(en_names_osm_address_path)

    df_wrong_street_names = pd.read_csv(os.path.join(qa_path, 'wrong_street_names.csv'), dtype={'ref:RS:ulica': 'string'})

    opstine = []
    total = {
        'unneeded_name_en': 0,
        'suspicious_name_en': 0,
    }

    df_wrong_street_names = df_wrong_street_names[
        df_wrong_street_names.suspicious_name_en |
        df_wrong_street_names.unneeded_name_en
    ]

    for opstina_name, df_wrong_street_names_in_opstina in df_wrong_street_names.sort_values('opstina_imel').groupby('opstina_imel'):
        suspicious_name_en_count = len(df_wrong_street_names_in_opstina[df_wrong_street_names_in_opstina.suspicious_name_en])
        unneeded_name_en_count = len(df_wrong_street_names_in_opstina[df_wrong_street_names_in_opstina.unneeded_name_en])

        total['unneeded_name_en'] += unneeded_name_en_count
        total['suspicious_name_en'] += suspicious_name_en_count
        opstine.append({
            'name': opstina_name,
            'unneeded_name_en': unneeded_name_en_count,
            'suspicious_name_en': suspicious_name_en_count,
        })
        streets = []

        opstina_html_path = os.path.join(en_names_osm_address_path, f'{opstina_name}.html')
        if os.path.exists(opstina_html_path):
            print(f"Page data/report/en_names/{opstina_name}.html already exists")
            continue

        print(f"Generating data/report/en_names/{opstina_name}.html")

        for _, df_street in df_wrong_street_names_in_opstina.iterrows():
            osm_id = df_street['osm_id']
            osm_type = 'way' if osm_id[0] == 'w' else 'relation' if osm_id[0] == 'r' else 'node'

            street = {
                'osm_link': f'https://openstreetmap.org/{osm_type}/{osm_id[1:]}',
                'osm_id': osm_id,
                'has_ref_rs_ulica': True if pd.notna(df_street['ref:RS:ulica']) and df_street['ref:RS:ulica'] else False,
                'osm_name': df_street['osm_name'] if pd.notna(df_street['osm_name']) else '',
                'osm_name_en': df_street['osm_name_en'],
                'unneeded_name_en': df_street['unneeded_name_en'],
                'suspicious_name_en': df_street['suspicious_name_en'],
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
        print("Page data/report/en_names.html already exists")
        return

    print("Generating data/report/en_names.html")

    for i, file in enumerate(sorted(os.listdir(analysis_path))):
        if not file.endswith(".csv"):
            continue
        opstina_name = file[:-4]
        if not any(o for o in opstine if o['name'] == opstina_name):
            opstine.append({
                'name': opstina_name,
                'unneeded_name_en': 0,
                'suspicious_name_en': 0,
            })
            output = template.render(
                currentDate=context['dates']['short'],
                reportDate=context['dates']['report'],
                osmDataDate=context['dates']['osm_data'],
                rgzDataDate=context['dates']['rgz_data'],
                streets=[],
                opstina_name=opstina_name,
            )
            opstina_html_path = os.path.join(en_names_osm_address_path, f'{opstina_name}.html')
            with open(opstina_html_path, 'w', encoding='utf-8') as fh:
                fh.write(output)

    template = env.get_template('qa/en_names.html.tpl')
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


def generate_int_names_report(context):
    env = context['env']
    cwd = context['cwd']

    qa_path = os.path.join(cwd, 'data/qa')
    analysis_path = os.path.join(cwd, 'data/analysis')
    report_path = os.path.join(cwd, 'data/report')
    html_path = os.path.join(report_path, 'int_names.html')
    int_names_osm_address_path = os.path.join(report_path, 'int_names')

    template = env.get_template('qa/int_names_opstina.html.tpl')

    if not os.path.exists(int_names_osm_address_path):
        os.mkdir(int_names_osm_address_path)

    df_wrong_street_names = pd.read_csv(os.path.join(qa_path, 'wrong_street_names.csv'), dtype={'ref:RS:ulica': 'string'})

    opstine = []
    total = {
        'wrong_int_name': 0,
        'missing_int_name': 0,
    }

    df_wrong_street_names = df_wrong_street_names[
        df_wrong_street_names.wrong_int_name |
        df_wrong_street_names.missing_int_name
    ]

    for opstina_name, df_wrong_street_names_in_opstina in df_wrong_street_names.sort_values('opstina_imel').groupby('opstina_imel'):
        wrong_int_name_count = len(df_wrong_street_names_in_opstina[df_wrong_street_names_in_opstina.wrong_int_name])
        missing_int_name_count = len(df_wrong_street_names_in_opstina[df_wrong_street_names_in_opstina.missing_int_name])

        total['wrong_int_name'] += wrong_int_name_count
        total['missing_int_name'] += missing_int_name_count
        opstine.append({
            'name': opstina_name,
            'wrong_int_name': wrong_int_name_count,
            'missing_int_name': missing_int_name_count,
        })
        streets = []

        opstina_html_path = os.path.join(int_names_osm_address_path, f'{opstina_name}.html')
        if os.path.exists(opstina_html_path):
            print(f"Page data/report/int_names/{opstina_name}.html already exists")
            continue

        print(f"Generating data/report/int_names/{opstina_name}.html")

        for _, df_street in df_wrong_street_names_in_opstina.iterrows():
            osm_id = df_street['osm_id']
            osm_type = 'way' if osm_id[0] == 'w' else 'relation' if osm_id[0] == 'r' else 'node'

            if pd.notna(df_street['rgz_ulica_proper']) and df_street['rgz_ulica_proper'] != '':
                osm_int_name_proper = cyr2intname(df_street['rgz_ulica_proper'])
            else:
                if pd.notna(df_street['osm_name']):
                    osm_int_name_proper = cyr2intname(df_street['osm_name'])
                else:
                    osm_int_name_proper = '?'

            street = {
                'osm_link': f'https://openstreetmap.org/{osm_type}/{osm_id[1:]}',
                'osm_id': osm_id,
                'has_ref_rs_ulica': True if pd.notna(df_street['ref:RS:ulica']) and df_street['ref:RS:ulica'] else False,
                'osm_name': df_street['osm_name'] if pd.notna(df_street['osm_name']) else '',
                'osm_int_name': df_street['osm_int_name'],
                'osm_int_name_proper': osm_int_name_proper,
                'wrong_int_name': df_street['wrong_int_name'],
                'missing_int_name': df_street['missing_int_name'],
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
        print("Page data/report/int_names.html already exists")
        return

    print("Generating data/report/int_names.html")

    for i, file in enumerate(sorted(os.listdir(analysis_path))):
        if not file.endswith(".csv"):
            continue
        opstina_name = file[:-4]
        if not any(o for o in opstine if o['name'] == opstina_name):
            opstine.append({
                'name': opstina_name,
                'wrong_int_name': 0,
                'missing_int_name': 0,
            })
            output = template.render(
                currentDate=context['dates']['short'],
                reportDate=context['dates']['report'],
                osmDataDate=context['dates']['osm_data'],
                rgzDataDate=context['dates']['rgz_data'],
                streets=[],
                opstina_name=opstina_name,
            )
            opstina_html_path = os.path.join(int_names_osm_address_path, f'{opstina_name}.html')
            with open(opstina_html_path, 'w', encoding='utf-8') as fh:
                fh.write(output)

    template = env.get_template('qa/int_names.html.tpl')
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


def emphasise_partial_alt_suggestion(s: str):
    if pd.isna(s):
        return s
    idx1 = s.find('~~')
    if idx1 == -1:
        return s
    idx2 = s.find('~~', idx1 + 1)
    if idx2 == -1:
        return s
    return s[0:idx1] + '<i>*' + s[idx1+2:idx2] + '*</i>' + s[idx2+2:]


def generate_alt_names_report(context):
    env = context['env']
    cwd = context['cwd']

    qa_path = os.path.join(cwd, 'data/qa')
    analysis_path = os.path.join(cwd, 'data/analysis')
    report_path = os.path.join(cwd, 'data/report')
    html_path = os.path.join(report_path, 'alt_names.html')
    alt_names_osm_address_path = os.path.join(report_path, 'alt_names')

    template = env.get_template('qa/alt_names_opstina.html.tpl')

    if not os.path.exists(alt_names_osm_address_path):
        os.mkdir(alt_names_osm_address_path)

    df_wrong_alt_names = pd.read_csv(os.path.join(qa_path, 'wrong_alt_names.csv'), dtype={'ref:RS:ulica': 'string'})
    df_wrong_alt_names['ref:RS:ulica'] = df_wrong_alt_names['ref:RS:ulica'].astype(object).where(df_wrong_alt_names['ref:RS:ulica'].notnull(), np.nan)

    opstine = []
    total = {
        'wrong_alt_name': 0,
        'missing_alt_name': 0,
        'wrong_alt_name_sr': 0,
        'missing_alt_name_sr': 0,
        'wrong_alt_name_sr_latn': 0,
        'missing_alt_name_sr_latn': 0,
    }

    for opstina_name, df_wrong_alt_names_in_opstina in df_wrong_alt_names.sort_values('opstina_imel').groupby('opstina_imel'):
        wrong_alt_name_count = len(df_wrong_alt_names_in_opstina[df_wrong_alt_names_in_opstina.is_wrong_alt_name])
        missing_alt_name_count = len(df_wrong_alt_names_in_opstina[df_wrong_alt_names_in_opstina.is_missing_alt_name])
        wrong_alt_name_sr_count = len(df_wrong_alt_names_in_opstina[df_wrong_alt_names_in_opstina.is_wrong_alt_name_sr])
        missing_alt_name_sr_count = len(df_wrong_alt_names_in_opstina[df_wrong_alt_names_in_opstina.is_missing_alt_name_sr])
        wrong_alt_name_sr_latn_count = len(df_wrong_alt_names_in_opstina[df_wrong_alt_names_in_opstina.is_wrong_alt_name_sr_latn])
        missing_alt_name_sr_latn_count = len(df_wrong_alt_names_in_opstina[df_wrong_alt_names_in_opstina.is_missing_alt_name_sr_latn])

        total['wrong_alt_name'] += wrong_alt_name_count
        total['missing_alt_name'] += missing_alt_name_count
        total['wrong_alt_name_sr'] += wrong_alt_name_sr_count
        total['missing_alt_name_sr'] += missing_alt_name_sr_count
        total['wrong_alt_name_sr_latn'] += wrong_alt_name_sr_latn_count
        total['missing_alt_name_sr_latn'] += missing_alt_name_sr_latn_count

        opstine.append({
            'name': opstina_name,
            'wrong_alt_name': wrong_alt_name_count,
            'missing_alt_name': missing_alt_name_count,
            'wrong_alt_name_sr': wrong_alt_name_sr_count,
            'missing_alt_name_sr': missing_alt_name_sr_count,
            'wrong_alt_name_sr_latn': wrong_alt_name_sr_latn_count,
            'missing_alt_name_sr_latn': missing_alt_name_sr_latn_count,
        })

        streets = []
        opstina_html_path = os.path.join(alt_names_osm_address_path, f'{opstina_name}.html')
        if os.path.exists(opstina_html_path):
            print(f"Page data/report/alt_names/{opstina_name}.html already exists")
            continue

        print(f"Generating data/report/alt_names/{opstina_name}.html")

        for _, df_street in df_wrong_alt_names_in_opstina.iterrows():
            osm_id = df_street['osm_id']
            osm_type = 'way' if osm_id[0] == 'w' else 'relation' if osm_id[0] == 'r' else 'node'

            street = {
                'osm_link': f'https://openstreetmap.org/{osm_type}/{osm_id[1:]}',
                'osm_id': osm_id,
                'has_ref_rs_ulica': True if pd.notna(df_street['ref:RS:ulica']) and df_street['ref:RS:ulica'] else False,
                'ref_rs_ulica': df_street['ref:RS:ulica'] if pd.notna(df_street['ref:RS:ulica']) else '',
                'rgz_ulica_proper': df_street['rgz_ulica_proper'] if pd.notna(df_street['rgz_ulica_proper']) else '',
                'osm_name': df_street['osm_name'] if pd.notna(df_street['osm_name']) else '',
                'osm_alt_name': df_street['osm_alt_name'],
                'osm_alt_name_sr': df_street['osm_alt_name_sr'],
                'osm_alt_name_sr_latn': df_street['osm_alt_name_sr_latn'],

                'is_missing_alt_name': df_street['is_missing_alt_name'],
                'is_wrong_alt_name': df_street['is_wrong_alt_name'],
                'alt_name_suggestion': emphasise_partial_alt_suggestion(df_street['alt_name_suggestion']),
                'is_alt_name_suggestion_partial': df_street['is_alt_name_suggestion_partial'],

                'is_missing_alt_name_sr': df_street['is_missing_alt_name_sr'],
                'is_wrong_alt_name_sr': df_street['is_wrong_alt_name_sr'],
                'alt_name_sr_suggestion': emphasise_partial_alt_suggestion(df_street['alt_name_sr_suggestion']),
                'is_alt_name_sr_suggestion_partial': df_street['is_alt_name_sr_suggestion_partial'],

                'is_missing_alt_name_sr_latn': df_street['is_missing_alt_name_sr_latn'],
                'is_wrong_alt_name_sr_latn': df_street['is_wrong_alt_name_sr_latn'],
                'alt_name_sr_latn_suggestion': emphasise_partial_alt_suggestion(df_street['alt_name_sr_latn_suggestion']),
                'is_alt_name_sr_latn_suggestion_partial': df_street['is_alt_name_sr_latn_suggestion_partial'],
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
        print("Page data/report/alt_names.html already exists")
        return

    print("Generating data/report/alt_names.html")

    for i, file in enumerate(sorted(os.listdir(analysis_path))):
        if not file.endswith(".csv"):
            continue
        opstina_name = file[:-4]
        if not any(o for o in opstine if o['name'] == opstina_name):
            opstine.append({
                'name': opstina_name,
                'wrong_alt_name': 0,
                'missing_alt_name': 0,
                'wrong_alt_name_sr': 0,
                'missing_alt_name_sr': 0,
                'wrong_alt_name_sr_latn': 0,
                'missing_alt_name_sr_latn': 0,
            })
            output = template.render(
                currentDate=context['dates']['short'],
                reportDate=context['dates']['report'],
                osmDataDate=context['dates']['osm_data'],
                rgzDataDate=context['dates']['rgz_data'],
                streets=[],
                opstina_name=opstina_name,
            )
            opstina_html_path = os.path.join(alt_names_osm_address_path, f'{opstina_name}.html')
            with open(opstina_html_path, 'w', encoding='utf-8') as fh:
                fh.write(output)

    template = env.get_template('qa/alt_names.html.tpl')
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
    generate_english_names_report(context)
    generate_int_names_report(context)
    generate_alt_names_report(context)

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
