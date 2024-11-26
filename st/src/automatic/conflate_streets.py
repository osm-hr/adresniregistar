# -*- coding: utf-8 -*-

import argparse
import os
import time

import osmapi
import pandas as pd
from requests_oauthlib import OAuth2Session

from common import token_loader, save_and_get_access_token
from street_mapping import StreetMapping

INTERACTIVE = False  # Change if you know what are you doing


def do_opstina(data_path, street_mappings: StreetMapping, opstina, oauth_session: OAuth2Session):
    print(f"Doing opstina {opstina}")

    api = osmapi.OsmApi(session=oauth_session)
    api.ChangesetCreate({
        "comment": f"RGZ address import in {opstina} (adding ref:RS:ulica to existing ways, https://community.openstreetmap.org/t/topic/9338/18)",
        "tag": "mechanical=yes",
        "source": "RGZ_ST"
    })

    analysis_path = os.path.join(data_path, 'analysis')
    opstina_csv_filepath = os.path.join(analysis_path,  f'{opstina.upper()}.csv')
    if not os.path.exists(opstina_csv_filepath):
        raise Exception(f"Missing file {os.path.relpath(opstina_csv_filepath)}")

    df_opstina = pd.read_csv(opstina_csv_filepath, dtype={'conflated_osm_way_length': object})
    df_opstina['rgz_ulica_mb'] = df_opstina['rgz_ulica_mb'].astype('str')
    df_opstina = df_opstina[~df_opstina.is_zaseok]
    df_opstina = df_opstina[df_opstina.rgz_ulica_mb.str[6] != '2']
    only_matched_addresses = df_opstina[pd.notna(df_opstina.found_osm_id)]
    i = 0
    for _, address in only_matched_addresses.sort_values(['rgz_ulica']).iterrows():
        i = i + 1
        for found_way_id, name_match, norm_name_match in zip(address.found_osm_id.split(','), address.name_match.split(','),  address.norm_name_match.split(',')):
            if name_match != '1' and norm_name_match != '1':
                continue

            if found_way_id[0] == 'n':
                print(f"Encountered node {found_way_id}, not expecting this... ", end='')
                continue
            if found_way_id[0] == 'r':
                print(f"Encountered relation {found_way_id}, had to be merged manually... ", end='')
                continue

            way_id = int(found_way_id[1:])
            try:
                entity = api.WayGet(way_id)
            except osmapi.errors.ElementDeletedApiError:
                continue
            time.sleep(0.1)

            if 'name' not in entity['tag']:
                continue
            current_street_name = entity['tag']['name']

            print(f'https://www.openstreetmap.org/way/{way_id}')
            if 'ref:RS:ulica' in entity['tag']:
                print(f"Already done {current_street_name}, skipping")
                continue

            entity['tag']['ref:RS:ulica'] = str(address.rgz_ulica_mb)
            accepted = False

            while True:
                if INTERACTIVE:
                    response = input(f"({i}/{len(only_matched_addresses)}) Are you sure you want to add ref:RS:ulica={str(address.rgz_ulica_mb)} to {current_street_name} (Y/n/c)?")
                else:
                    print(f"({i}/{len(only_matched_addresses)}) +ref:RS:ulica={str(address.rgz_ulica_mb)} @ {current_street_name}")
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


def do_all_opstina(data_path, street_mappings, oauth_session: OAuth2Session):
    osm_csv_path = os.path.join(data_path, 'osm/csv')
    df_rgz_per_opstina = []
    for i, file in enumerate(sorted(os.listdir(osm_csv_path))):
        if not file.endswith(".csv"):
            continue
        input_osm_file = os.path.join(osm_csv_path, f'{file[:-4]}.csv')
        do_opstina(data_path, street_mappings, file[:-4], oauth_session)


def main():
    cwd = os.getcwd()
    data_path = os.path.join(cwd, 'data')

    parser = argparse.ArgumentParser(
        description='conflate_streets.py - Adds ref:RS:ulica to ways it is possible to do so')
    parser.add_argument('--opstina', default='', required=False, help='Opstina to process')
    args = parser.parse_args()

    print("Loading normalized street names mapping")
    street_mappings = StreetMapping(os.path.join(cwd, '..', 'ar'))

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

    if args.opstina != '':
        do_opstina(data_path, street_mappings, args.opstina, oauth_session)
    else:
        do_all_opstina(data_path, street_mappings, oauth_session)


if __name__ == '__main__':
    main()
