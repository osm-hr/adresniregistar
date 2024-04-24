# -*- coding: utf-8 -*-

import argparse
import os
import time

import osmapi
import pandas as pd
import ast

from common import ApartmentResolution
import numpy as np

INTERACTIVE = True  # Change if you know what are you doing


suggestion_db = {}


def fix_apartments(data_path, opstina: str=None):
    if opstina:
        print(f"Doing opstina {opstina}")
    else:
        print("Doing all opstina")

    additional_comment = ''
    if opstina:
        additional_comment = f'in {opstina} '
    api = osmapi.OsmApi(passwordfile='osm-password', changesetauto=True, changesetautosize=1000 if opstina else 100, changesetautotags={
        "comment": f"RGZ apartment fixing {additional_comment}(automatically setting building=apartments, https://community.openstreetmap.org/t/registar-stambenih-zajednica-otvoreni-podaci/87583/27)",
        "tag": "mechanical=yes",
        "source": "RGZ_SZ"
    })

    df_data = pd.read_csv(os.path.join(data_path, 'sz_analysis.csv'))
    df_data['resolution'] = df_data['resolution'].apply(lambda x: ApartmentResolution(x) if pd.notna(x) else np.nan)
    if opstina:
        df_data = df_data[df_data.sz_opstina == opstina]

    df_data = df_data[df_data.resolution == ApartmentResolution.OSM_ENTITY_NOT_APARTMENT]

    fixed_buildings=set()
    i = 0
    potentially_fixed = 0
    for _, wrong_address in df_data.sort_values(['sz_opstina', 'osm_id']).iterrows():
        i = i + 1
        osm_ids_str = wrong_address['osm_id']

        osm_ids = ast.literal_eval(osm_ids_str)
        if len(osm_ids) > 1:
            print(f"There are multiple nodes {osm_ids_str} - resolve manually")
            continue

        osm_id = osm_ids[0]
        if osm_id[0] == 'r':
            print(f"Encountered relation {osm_id}, had to be merged manually... ", end='')
            continue

        closest_building = wrong_address['closest_building']
        if closest_building in fixed_buildings:
            print(f"Closest building {closest_building} already fixes, skipping")
            continue
        if closest_building[0] == 'n':
            print(f"Closest building for osm_id {osm_id} is node {closest_building}, resolve manually")
            continue
        if closest_building[0] == 'r':
            print(f"Closest building for osm_id {osm_id} is relation {closest_building}, resolve manually")
            continue

        try:
            entity_building_way = api.WayGet(closest_building[1:])
        except osmapi.errors.ElementDeletedApiError:
            continue
        time.sleep(0.1)

        if 'building' not in entity_building_way['tag']:
            print(f"Entity {osm_id} do not have building tag, skipping")
            continue
        if entity_building_way['tag']['building'] == 'apartments':
            print(f"Entity {osm_id} already tagged as apartments, skipping")
            continue
        if entity_building_way['tag']['building'] == 'construction':
            if 'construction' in entity_building_way['tag'] and entity_building_way['tag']['construction'] == 'apartments':
                print(f"Entity {osm_id} already tagged as apartments, skipping")
                continue
        if entity_building_way['tag']['building'] not in ('house', 'yes', 'residential', 'terrace', 'construction'):
            print(f"Entity {entity_building_way} tagged as building={entity_building_way['tag']['building']}, skipping unknown building value")
            continue

        print(f'({i}/{len(df_data)}) Building https://www.openstreetmap.org/way/{entity_building_way["id"]} with building={entity_building_way["tag"]["building"]}')

        accepted = False

        while True:
            if INTERACTIVE:
                response = input(f"Are you sure you want to change building={entity_building_way['tag']['building']} to apartments (Y/n/c)?")
            else:
                print(f"Are you sure you want to change building={entity_building_way['tag']['building']} to apartments?")
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

        if entity_building_way['tag']['building'] == 'construction':
            entity_building_way['tag']['construction'] = 'apartments'
        else:
            entity_building_way['tag']['building'] = 'apartments'
        potentially_fixed += 1
        api.WayUpdate(entity_building_way)
        fixed_buildings.add(closest_building)
        print(f"Processed {i}, potentially fixed: {potentially_fixed}")
    api.flush()


def main():
    cwd = os.getcwd()
    data_path = os.path.join(cwd, 'data')

    parser = argparse.ArgumentParser(
        description='fix_apartments.py - Tag buildings as apartments')
    parser.add_argument('--opstina', default='', required=False, help='Opstina to process')
    args = parser.parse_args()

    if args.opstina != '':
        fix_apartments(data_path, args.opstina)
    else:
        fix_apartments(data_path)


if __name__ == '__main__':
    main()
