# -*- coding: utf-8 -*-

import argparse
import os
import time

import osmapi
import pandas as pd

from street_mapping import StreetMapping
from common import cyr2lat_small

INTERACTIVE = True  # Change if you know what are you doing


suggestion_db = {}


def ask_for_fix(suggestion_db: dict, alt_name_suggestion: str):
    if alt_name_suggestion in suggestion_db:
        return suggestion_db[alt_name_suggestion]

    idx1 = alt_name_suggestion.find('~')
    idx2 = alt_name_suggestion.find('~', idx1+2)
    tilde_part = alt_name_suggestion[idx1:idx2+2]

    response = input(f"Write replacement for {tilde_part} in {alt_name_suggestion}: ")
    replacement = alt_name_suggestion[0:idx1] + response + alt_name_suggestion[idx2+2:]
    suggestion_db[alt_name_suggestion] = replacement
    alt_name_suggestion_latn = cyr2lat_small(alt_name_suggestion)
    if alt_name_suggestion != alt_name_suggestion_latn:
        suggestion_db[alt_name_suggestion_latn] = cyr2lat_small(replacement)
    return replacement


def fix_alt_names(data_path, street_mappings: StreetMapping, opstina: str=None):
    if opstina:
        print(f"Doing opstina {opstina}")
    else:
        print("Doing all opstina")

    additional_comment = ''
    if opstina:
        additional_comment = f'in {opstina} '
    api = osmapi.OsmApi(passwordfile='osm-password', changesetauto=True, changesetautosize=1000 if opstina else 100, changesetautotags={
        "comment": f"RGZ address import {additional_comment}(fixing name:sr and name:sr-Latn on conflated ways, https://community.openstreetmap.org/t/topic/9338/18)",
        "tag": "mechanical=yes",
        "source": "RGZ_ST"
    })

    qa_path = os.path.join(data_path, 'qa')
    df_wrong_alt_names = pd.read_csv(os.path.join(qa_path, 'wrong_alt_names.csv'))
    df_wrong_alt_names = df_wrong_alt_names[pd.notna(df_wrong_alt_names['ref:RS:ulica'])]
    df_wrong_alt_names = df_wrong_alt_names[df_wrong_alt_names.osm_name == df_wrong_alt_names.rgz_ulica_proper]
    if opstina:
        df_wrong_alt_names = df_wrong_alt_names[df_wrong_alt_names.opstina_imel == opstina]
    df_wrong_alt_names = df_wrong_alt_names[
        df_wrong_alt_names.is_wrong_alt_name | df_wrong_alt_names.is_missing_alt_name |
        df_wrong_alt_names.is_wrong_alt_name_sr | df_wrong_alt_names.is_missing_alt_name_sr |
        df_wrong_alt_names.is_wrong_alt_name_sr_latn | df_wrong_alt_names.is_missing_alt_name_sr_latn]

    i = 0
    visited_streets = set()
    for _, street in df_wrong_alt_names.sort_values(['osm_id']).iterrows():
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
        time.sleep(0.1)

        if 'name' not in entity['tag']:
            print(f"Entity {osm_id} do not have name, skipping")
            continue
        if 'ref:RS:ulica' not in entity['tag']:
            print(f"Entity {osm_id} do not have ref:RS:ulica, skipping")
            continue

        current_street_name = entity['tag']['name']

        print(f'({i}/{len(df_wrong_alt_names)}) https://www.openstreetmap.org/way/{way_id}')
        any_change = False
        if street['is_wrong_alt_name']:
            old_alt_name = street['osm_alt_name']
            if old_alt_name == entity['tag']['alt_name']:
                if street['is_alt_name_suggestion_partial']:
                    proper_alt_name = ask_for_fix(suggestion_db, street['alt_name_suggestion'])
                else:
                    proper_alt_name = street['alt_name_suggestion']
                print(f'alt_name={old_alt_name} => {proper_alt_name} (name="{current_street_name}")')
                entity['tag']['alt_name'] = proper_alt_name
                any_change = True
        if street['is_missing_alt_name']:
            if 'alt_name' not in entity['tag']:
                if street['is_alt_name_suggestion_partial']:
                    proper_alt_name = ask_for_fix(suggestion_db, street['alt_name_suggestion'])
                else:
                    proper_alt_name = street['alt_name_suggestion']
                print(f'+alt_name={proper_alt_name} (name="{current_street_name}")')
                entity['tag']['alt_name'] = proper_alt_name
                any_change = True
        if street['is_wrong_alt_name_sr']:
            old_alt_name_sr = street['osm_alt_name_sr']
            if old_alt_name_sr == entity['tag']['alt_name:sr']:
                if street['is_alt_name_sr_suggestion_partial']:
                    proper_alt_name_sr = ask_for_fix(suggestion_db, street['alt_name_sr_suggestion'])
                else:
                    proper_alt_name_sr = street['alt_name_sr_suggestion']
                print(f'alt_name:sr={old_alt_name_sr} => {proper_alt_name_sr} (name="{current_street_name}")')
                entity['tag']['alt_name:sr'] = proper_alt_name_sr
                any_change = True
        if street['is_missing_alt_name_sr']:
            if 'alt_name:sr' not in entity['tag']:
                if street['is_alt_name_sr_suggestion_partial']:
                    proper_alt_name_sr = ask_for_fix(suggestion_db, street['alt_name_sr_suggestion'])
                else:
                    proper_alt_name_sr = street['alt_name_sr_suggestion']
                print(f'+alt_name:sr={proper_alt_name_sr} (name="{current_street_name}")')
                entity['tag']['alt_name:sr'] = proper_alt_name_sr
                any_change = True
        if street['is_wrong_alt_name_sr_latn']:
            old_alt_name_sr_latn = street['osm_alt_name_sr_latn']
            if old_alt_name_sr_latn == entity['tag']['alt_name:sr-Latn']:
                if street['is_alt_name_sr_latn_suggestion_partial']:
                    proper_alt_name_sr_latn = ask_for_fix(suggestion_db, street['alt_name_sr_latn_suggestion'])
                else:
                    proper_alt_name_sr_latn = street['alt_name_sr_latn_suggestion']
                print(f'alt_name:sr-Latn={old_alt_name_sr_latn} => {proper_alt_name_sr_latn} (name="{current_street_name}")')
                entity['tag']['alt_name:sr-Latn'] = proper_alt_name_sr_latn
                any_change = True
        if street['is_missing_alt_name_sr_latn']:
            if 'alt_name:sr-Latn' not in entity['tag']:
                if street['is_alt_name_sr_latn_suggestion_partial']:
                    proper_alt_name_sr_latn = ask_for_fix(suggestion_db, street['alt_name_sr_latn_suggestion'])
                else:
                    proper_alt_name_sr_latn = street['alt_name_sr_latn_suggestion']
                print(f'+alt_name:sr={proper_alt_name_sr_latn} (name="{current_street_name}")')
                entity['tag']['alt_name:sr-Latn'] = proper_alt_name_sr_latn
                any_change = True

        if not any_change:
            continue
        accepted = False

        while True:
            if INTERACTIVE:
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
        description='fix_names.py - Adds proper name:sr and name:sr-Latn to conflated ways')
    parser.add_argument('--opstina', default='', required=False, help='Opstina to process')
    args = parser.parse_args()

    print("Loading normalized street names mapping")
    street_mappings = StreetMapping(os.path.join(cwd, '..', 'ar'))

    if args.opstina != '':
        fix_alt_names(data_path, street_mappings, args.opstina)
    else:
        fix_alt_names(data_path, street_mappings)


if __name__ == '__main__':
    main()
