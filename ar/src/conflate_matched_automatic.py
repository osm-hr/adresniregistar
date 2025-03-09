# -*- coding: utf-8 -*-

import argparse
import os
import time

import osmapi
import pandas as pd

from common import load_mappings, normalize_name_latin, cyr2lat
from street_mapping import StreetMapping

INTERACTIVE = False  # Change if you know what are you doing


def fix_wrong_streetname():
    api = osmapi.OsmApi(passwordfile='osm-password', changesetauto=True, changesetautosize=100, changesetautotags={
        "comment": f"RGZ address import (fixing wrong/mistyped addr:street)",
        "tag": "mechanical=yes",
        "source": "RGZ_AR"
    })

    accepted_streets, declined_streets = set(), set()
    declined_streets.add(('БРАНИСЛАВА НУШИЋА', 'Павла Савића'))
    declined_streets.add(('ЖИЧКА', 'Церска'))
    declined_streets.add(('ЖАНА НИКОЛИЋА', 'Жане Николић'))
    declined_streets.add(('КОЛАШИНСКА', 'Браће Јевремовић'))
    declined_streets.add(('НИКОЛЕТИНЕ БУРСАЋА', 'Друге пролетерске бригаде'))
    declined_streets.add(('КОВИНСКА', 'Лазе Симића'))

    df_osm_qa = pd.read_csv('data/qa/osm_import_qa-full.csv')
    df_osm_qa = df_osm_qa[~df_osm_qa['street_perfect_match']]
    #df_osm_qa = df_osm_qa[~df_osm_qa['street_partial_match']]
    i = 0
    for _, problem in df_osm_qa.iterrows():
        i = i + 1
        entity_id = int(problem.osm_id[1:])
        if problem.osm_id[0] == 'n':
            entity_type = 'node'
            entity = api.NodeGet(entity_id)
        elif problem.osm_id[0] == 'w':
            entity_type = 'way'
            entity = api.WayGet(entity_id)
        else:
            entity_type = "relation"
            entity = api.RelationGet(entity_id)

        if 'addr:street' in entity['tag'] and entity['tag']['addr:street'] == problem['rgz_ulica_proper']:
            print(f"Already done {entity['tag']['addr:street']} {entity['tag']['addr:housenumber']}, skipping")
            continue
        print(f'https://www.openstreetmap.org/{entity_type}/{entity_id}')

        if 'addr:street' not in entity['tag']:
            print(f"Missing addr:street for https://www.openstreetmap.org/{entity_type}/{entity_id}, skipping")
            continue

        print(f"({i}/{len(df_osm_qa)}) addr:street changed from '{entity['tag']['addr:street']}' => \t'{problem['rgz_ulica_proper']}' (RGZ: {problem['rgz_ulica']})")
        accepted = False
        while True:
            is_accepted = (problem['rgz_ulica'], entity['tag']['addr:street']) in accepted_streets
            is_declined = (problem['rgz_ulica'], entity['tag']['addr:street']) in declined_streets
            if is_declined:
                response = 'n'
            elif is_accepted:
                response = 'y'
            else:
                response = input('?')
            if response == '' or response.lower() == 'y' or response.lower() == u'з':
                accepted = True
                accepted_streets.add((problem['rgz_ulica'], entity['tag']['addr:street']))
            elif response.lower() == u'c' or response.lower() == u'ц':
                new_answer = input('Again: ')
                if new_answer == '':
                    continue
                else:
                    accepted = True
            else:
                declined_streets.add((problem['rgz_ulica'], entity['tag']['addr:street']))
            break
        if not accepted:
            continue
        entity['tag']['addr:street'] = problem['rgz_ulica_proper']
        if entity_type == 'node':
            api.NodeUpdate(entity)
        elif entity_type == "way":
            api.WayUpdate(entity)
        else:
            api.RelationUpdate(entity)
        time.sleep(0.1)
    api.flush()


def do_opstina(data_path, street_mappings: StreetMapping, opstina):
    analysis_path = os.path.join(data_path, 'analysis')
    opstina_csv_filepath = os.path.join(analysis_path,  f'{opstina.upper()}.csv')
    if not os.path.exists(opstina_csv_filepath):
        raise Exception(f"Missing file {os.path.relpath(opstina_csv_filepath)}")
    df_opstina = pd.read_csv(os.path.join(analysis_path, opstina_csv_filepath), dtype={'conflated_osm_housenumber': object, 'osm_housenumber': object})
    for naselje_name, df_naselje in df_opstina.groupby('rgz_naselje'):
        naselje_name_lat = cyr2lat(naselje_name)
        print(f"Processing municipality {opstina} and settlement {naselje_name_lat}")
        api = osmapi.OsmApi(passwordfile='osm-password', changesetauto=True, changesetautosize=100, changesetautotags={
            "comment": f"RGZ address import in {opstina}/{naselje_name_lat} (adding ref:RS:kucni_broj to existing addresses, https://lists.openstreetmap.org/pipermail/imports/2023-March/007187.html)",
            "tag": "mechanical=yes",
            "source": "RGZ_AR"
        })

        i = 0
        only_matched_addresses = df_naselje[pd.isna(df_naselje.conflated_osm_id) & pd.notna(df_naselje.osm_id)]
        for _, address in only_matched_addresses.sort_values(['rgz_ulica', 'rgz_kucni_broj']).iterrows():
            i = i + 1
            if address.osm_id[0] == 'r':
                print(f"Encountered relation {address.osm_id}, had to be merged manually... ", end='')
                continue
            if address.distance > 50:
                print(f"Distance is {address.distance}m - too much, skipping")
                continue
            if address.distance > 20 and not address.matching:
                print(f"Distance is {address.distance}m - too much when not matching, skipping")
                continue
            entity_id = int(address.osm_id[1:])
            rgz_kucni_broj = str(address.rgz_kucni_broj_id)
            if address.osm_id[0] == 'n':
                entity_type = 'node'
            elif address.osm_id[0] == 'w':
                entity_type = 'way'
            else:
                raise Exception("Unknown entity")

            if entity_type == 'node':
                entity = api.NodeGet(entity_id)
            else:
                entity = api.WayGet(entity_id)

            if 'ref:RS:kucni_broj' in entity['tag']:
                print(f"Already done {entity['tag']['addr:street']} {entity['tag']['addr:housenumber']}, skipping")
                continue

            print(f'https://www.openstreetmap.org/{entity_type}/{entity_id}')
            accepted = False
            current_street_name = entity['tag']['addr:street'] if 'addr:street' in entity['tag'] else 'n/a'

            while True:
                if INTERACTIVE:
                    response = input(f"({i}/{len(df_naselje)}) Are you sure you want to add ref:RS:kucni_broj={rgz_kucni_broj} to {current_street_name} {entity['tag']['addr:housenumber']} (Y/n/c)?")
                else:
                    print(f"({i}/{len(df_naselje)}) +ref:RS:kucni_broj={rgz_kucni_broj} @ {current_street_name} {entity['tag']['addr:housenumber']}")
                    response = 'y'
                    time.sleep(1)
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

            entity['tag']['ref:RS:kucni_broj'] = rgz_kucni_broj

            # Check street name and ask for it
            proper_street_name = street_mappings.get_name(address['rgz_ulica'], '123')
            if proper_street_name != current_street_name and proper_street_name != '':
                if INTERACTIVE:
                    response = input(f"({i}/{len(df_naselje)}) Do you also want to change addr:street from {current_street_name} to {proper_street_name} (Y/n)?")
                else:
                    print(f"({i}/{len(df_naselje)}) Changing addr:street: {current_street_name} => {proper_street_name}")
                    response = 'y'
                    time.sleep(1)
                if response == '' or response.lower() == 'y' or response.lower() == u'з':
                    entity['tag']['addr:street'] = proper_street_name

            # Check housenumber and ask for it
            proper_housenumber = normalize_name_latin(address['rgz_kucni_broj'])
            if proper_housenumber != entity['tag']['addr:housenumber']:
                if INTERACTIVE:
                    response = input(f"({i}/{len(df_naselje)}) Do you also want to change addr:housenumber from {entity['tag']['addr:housenumber']} to {proper_housenumber} (Y/n)?")
                else:
                    print(f"({i}/{len(df_naselje)}) Changing addr:housenumber: {entity['tag']['addr:housenumber']} => {proper_housenumber}")
                    response = 'y'
                    time.sleep(1)
                if response == '' or response.lower() == 'y' or response.lower() == u'з':
                    entity['tag']['addr:housenumber'] = proper_housenumber
            if entity_type == 'node':
                api.NodeUpdate(entity)
            else:
                api.WayUpdate(entity)
        print(f"Done with settlement {naselje_name_lat}")
        api.flush()


def main():
    cwd = os.getcwd()
    data_path = os.path.join(cwd, 'data')

    parser = argparse.ArgumentParser(
        description='create_analysis.py - Analyses opstine')
    parser.add_argument('--opstina', default=None, required=True, help='Opstina to process')
    args = parser.parse_args()
    if not args.opstina:
        raise Exception("Provide --opstina <opstina> argument")

    print("Loading normalized street names mapping")
    street_mappings = StreetMapping(cwd)

    do_opstina(data_path, street_mappings, args.opstina)
    #fix_wrong_streetname()


if __name__ == '__main__':
    main()
