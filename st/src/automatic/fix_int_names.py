# -*- coding: utf-8 -*-

import argparse
import os
import time

import osmapi
import pandas as pd

from street_mapping import StreetMapping
from common import cyr2intname

INTERACTIVE = True  # Change if you know what are you doing


suggestion_db = {}


def fix_int_names(data_path, street_mappings: StreetMapping, opstina: str=None):
    if opstina:
        print(f"Doing opstina {opstina}")
    else:
        print("Doing all opstina")

    additional_comment = ''
    if opstina:
        additional_comment = f'in {opstina} '
    api = osmapi.OsmApi(passwordfile='osm-password', changesetauto=True, changesetautosize=1000 if opstina else 100, changesetautotags={
        "comment": f"RGZ street import {additional_comment}(fixing and adding int_name on street names, https://community.openstreetmap.org/t/uvoz-adresnog-registra-pravila-tagovanja-ulica-u-srbiji/106126)",
        "tag": "mechanical=yes",
        "source": "RGZ_ST"
    })

    qa_path = os.path.join(data_path, 'qa')
    df_wrong_int_names = pd.read_csv(os.path.join(qa_path, 'wrong_street_names.csv'))
    if opstina:
        df_wrong_int_names = df_wrong_int_names[df_wrong_int_names.opstina_imel == opstina]
    df_wrong_int_names = df_wrong_int_names[df_wrong_int_names.wrong_int_name | df_wrong_int_names.missing_int_name]

    i = 0
    visited_streets = set()
    for _, street in df_wrong_int_names.sort_values(['osm_id']).iterrows():
        i = i + 1
        osm_id = street['osm_id']

        if osm_id in visited_streets:
            continue
        visited_streets.add(osm_id)

        if osm_id[0] == 'n':
            print(f"Encountered node {osm_id}, not expecting this... ", end='')
            continue
        if osm_id[0] == 'r':
            print(f"Encountered relation {osm_id}, had to be merged manually... ", end='')
            continue

        way_id = int(osm_id[1:])
        try:
            entity = api.WayGet(way_id)
        except osmapi.errors.ElementDeletedApiError:
            continue
        time.sleep(1)

        if 'name' not in entity['tag']:
            print(f"Entity {osm_id} do not have name, skipping")
            continue
        is_conflated = 'ref:RS:ulica' in entity['tag']

        current_street_name = entity['tag']['name']
        current_int_name = entity['tag']['int_name'] if 'int_name' in entity['tag'] else None

        print(f'({i}/{len(df_wrong_int_names)}) https://www.openstreetmap.org/way/{way_id}')
        if is_conflated:
            rgz_name = street['rgz_ulica_proper']
            if rgz_name != current_street_name:
                print(f"RGZ {rgz_name} and current name {current_street_name} do not match, skipping")
                continue
            proper_int_name = cyr2intname(rgz_name)
            if current_int_name and current_int_name == proper_int_name:
                print(f"Way {osm_id} already have proper int_name={proper_int_name}, skipping")
                continue
            if current_int_name:
                print(f"Changing int_name={current_int_name} => {proper_int_name} for way {rgz_name}")
            else:
                print(f"+int_name={proper_int_name}")
            entity['tag']['int_name'] = proper_int_name
        else:
            proper_int_name = cyr2intname(current_street_name)
            if current_int_name:
                if current_int_name == proper_int_name:
                    print(f"Way {osm_id} already have proper int_name={proper_int_name}, skipping")
                    continue
                print(f"NOT CONFLATED - Changing int_name={current_int_name} => {proper_int_name} for way {current_street_name}")
            else:
                print(f"NOT CONFLATED +int_name={proper_int_name}")
            for k in entity['tag'].keys():
                print(f"    {k}={entity['tag'][k]}")
            entity['tag']['int_name'] = proper_int_name
        accepted = False

        while True:
            if INTERACTIVE and not is_conflated:
                response = input(f"Are you sure you want to make these changes (Y/n/c)?")
            else:
                print(f"Are you sure you want to make these changes?")
                response = 'y'
            if response == '' or response.lower() == 'y' or response.lower() == u'з':
                accepted = True
            if response.lower() == u'c' or response.lower() == u'ц':
                new_answer = input('Again: ')
                if new_answer == '':
                    continue
                else:
                    accepted = True
            break
        if not accepted:
            continue
        api.WayUpdate(entity)
    api.flush()


def main():
    cwd = os.getcwd()
    data_path = os.path.join(cwd, 'data')

    parser = argparse.ArgumentParser(
        description='fix_int_names.py - Adds proper int_name or fixes existing int_name')
    parser.add_argument('--opstina', default='', required=False, help='Opstina to process')
    args = parser.parse_args()

    print("Loading normalized street names mapping")
    street_mappings = StreetMapping(os.path.join(cwd, '..', 'ar'))

    if args.opstina != '':
        fix_int_names(data_path, street_mappings, args.opstina)
    else:
        fix_int_names(data_path, street_mappings)


if __name__ == '__main__':
    main()
