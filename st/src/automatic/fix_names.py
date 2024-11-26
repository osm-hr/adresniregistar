# -*- coding: utf-8 -*-

import argparse
import os
import time

import osmapi
import pandas as pd
from requests_oauthlib import OAuth2Session

from common import cyr2lat_small, token_loader, save_and_get_access_token
from street_mapping import StreetMapping

INTERACTIVE = False  # Change if you know what are you doing


def fix_names(data_path, street_mappings: StreetMapping, oauth_session: OAuth2Session, opstina: str=None):
    if opstina:
        print(f"Doing opstina {opstina}")
    else:
        print("Doing all opstina")

    additional_comment = ''
    if opstina:
        additional_comment = f'in {opstina} '
    api = osmapi.OsmApi(session=oauth_session)
    api.ChangesetCreate({
        "comment": f"RGZ address import {additional_comment}(fixing name:sr and name:sr-Latn on conflated ways, https://community.openstreetmap.org/t/topic/9338/18)",
        "tag": "mechanical=yes",
        "source": "RGZ_ST"
    })

    qa_path = os.path.join(data_path, 'qa')
    df_wrong_names = pd.read_csv(os.path.join(qa_path, 'wrong_street_names.csv'))
    df_wrong_names = df_wrong_names[pd.notna(df_wrong_names['ref:RS:ulica'])]
    df_wrong_names = df_wrong_names[~df_wrong_names.wrong_name]
    df_wrong_names = df_wrong_names[~df_wrong_names.missing_name]
    if opstina:
        df_wrong_names = df_wrong_names[df_wrong_names.opstina_imel == opstina]
    df_wrong_names = df_wrong_names[df_wrong_names.wrong_name_sr | df_wrong_names.missing_name_sr | df_wrong_names.wrong_name_sr_latn | df_wrong_names.missing_name_sr_latn]

    i = 0
    visited_streets = set()
    for _, street in df_wrong_names.sort_values(['rgz_ulica']).iterrows():
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

        print(f'({i}/{len(df_wrong_names)}) https://www.openstreetmap.org/way/{way_id}')
        any_change = False
        if street['wrong_name_sr']:
            old_name_sr = street['osm_name_sr']
            if old_name_sr == entity['tag']['name:sr']:
                proper_name_sr = entity['tag']['name']
                print(f'name:sr={old_name_sr} => {proper_name_sr} (name="{current_street_name}")')
                entity['tag']['name:sr'] = proper_name_sr
                any_change = True
        if street['missing_name_sr']:
            if 'name:sr' not in entity['tag']:
                proper_name_sr = entity['tag']['name']
                print(f'+name:sr={proper_name_sr} (name="{current_street_name}")')
                entity['tag']['name:sr'] = proper_name_sr
                any_change = True
        if street['wrong_name_sr_latn']:
            old_name_sr_latn = street['osm_name_sr_latn']
            if old_name_sr_latn == entity['tag']['name:sr-Latn']:
                proper_name_sr_latn = cyr2lat_small(entity['tag']['name'])
                print(f'name:sr-Latn={old_name_sr_latn} => {proper_name_sr_latn} (name="{current_street_name}")')
                entity['tag']['name:sr-Latn'] = proper_name_sr_latn
                any_change = True
        if street['missing_name_sr_latn']:
            if 'name:sr-Latn' not in entity['tag']:
                proper_name_sr_latn = cyr2lat_small(entity['tag']['name'])
                print(f'+name:sr-Latn={proper_name_sr_latn} (name="{current_street_name}")')
                entity['tag']['name:sr-Latn'] = proper_name_sr_latn
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
    api.ChangesetClose()


def main():
    cwd = os.getcwd()
    data_path = os.path.join(cwd, 'data')

    if not os.path.exists("client_secrets"):
        print("File 'client_secrets' is missing. Create OAuth2 application on 'https://www.openstreetmap.org/oauth2/applications' with redirect url 'urn:ietf:wg:oauth:2.0:oob' and all permissions and write <client_id>:<client_secret> in 'client_secrets' file before proceding")
        return
    with open('client_secrets') as f:
        client_id, client_secret = f.readline().split(":")

    try:
        token = token_loader()
    except FileNotFoundError:

        print("Token not found, get a new one...")
        token = save_and_get_access_token(client_id, client_secret, ["write_api", "write_notes"])
    oauth_session = OAuth2Session(client_id, token=token)


    parser = argparse.ArgumentParser(
        description='fix_names.py - Adds proper name:sr and name:sr-Latn to conflated ways')
    parser.add_argument('--opstina', default='', required=False, help='Opstina to process')
    args = parser.parse_args()

    print("Loading normalized street names mapping")
    street_mappings = StreetMapping(os.path.join(cwd, '..', 'ar'))

    if args.opstina != '':
        fix_names(data_path, street_mappings, oauth_session, args.opstina)
    else:
        fix_names(data_path, street_mappings, oauth_session)


if __name__ == '__main__':
    main()
