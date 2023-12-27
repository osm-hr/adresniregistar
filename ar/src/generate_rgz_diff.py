# -*- coding: utf-8 -*-

import argparse
import csv
import os
import sys
import time

import osmapi
import overpy
import pyproj
from shapely import wkt
from shapely.ops import transform

from common import load_mappings, normalize_name_latin

csv.field_size_limit(sys.maxsize)

wgs84 = pyproj.CRS('EPSG:4326')
utm = pyproj.CRS('EPSG:32634')
project = pyproj.Transformer.from_crs(utm, wgs84, always_xy=True).transform


def load_addresses(addresses_csv_path):
    results = {}
    with open(addresses_csv_path, encoding='utf=8') as addresses_csv_file:
        reader = csv.DictReader(addresses_csv_file)

        for row in reader:
            results[row['rgz_kucni_broj_id']] = {
                'kucni_broj_id': row['rgz_kucni_broj_id'],
                'opstina_mb': row['rgz_opstina_mb'],
                'opstina': row['rgz_opstina'],
                'naselje_mb': row['rgz_naselje_mb'],
                'naselje': row['rgz_naselje'],
                'ulica_mb': row['rgz_ulica_mb'],
                'ulica': row['rgz_ulica'],
                'kucni_broj': row['rgz_kucni_broj'],
                'geometry': transform(project, wkt.loads(row['rgz_geometry'])),
            }
    return results


def find_in_new_addresses(new_addresses, ulica_old, kucni_broj_old, geometry_old):
    for new_address in new_addresses:
        if new_address['ulica'] == ulica_old and new_address['kucni_broj'] == kucni_broj_old and new_address['geometry'].distance(geometry_old) < 100:
            return new_address
    return None


def get_ref_kucni_broj_from_overpass(overpass_api, kucni_broj_id):
    response = overpass_api.query(f"""
        [out:json];
        (
          nwr["ref:RS:kucni_broj"="{kucni_broj_id}"];
        );
        out body;
        // &contact=https://gitlab.com/osm-serbia/adresniregistar
    """)
    results = []
    for n in response.nodes:
        results.append('n' + str(n.id))
    for w in response.ways:
        results.append('w' + str(w.id))
    for r in response.relations:
        results.append('r' + str(r.id))
    return results


def fix_deleted_to_added(rgz_path, rgz_last_update):
    """
    Nalazi kucne brojeve koji su obrisani i koji su onda dodati sa novim ref:RS:kucni_broj,
    sa istim imenom ulice i kucnim brojom i unutar 100m i update-uje im ref:RS:kucni_broj
    """
    api = osmapi.OsmApi(passwordfile='osm-password', changesetauto=True, changesetautosize=100, changesetautotags={
        "comment": f"RGZ address import (updating ref:RS:kucni_broj after cadastre refresh), https://lists.openstreetmap.org/pipermail/imports/2023-March/007187.html",
        "tag": "mechanical=yes",
        "source": "RGZ_AR"
    })
    overpass_api = overpy.Overpass(url='http://localhost:12346/api/interpreter')

    print('Loading added addresses')
    new_addresses = []
    with open(os.path.join(rgz_path, 'addresses-added.csv'), encoding='utf=8') as addresses_new_file:
        reader = csv.DictReader(addresses_new_file)

        for row in reader:
            new_addresses.append({
                'kucni_broj_id': row['kucni_broj_id'],
                'opstina_mb': row['opstina_mb'],
                'opstina': row['opstina'],
                'naselje_mb': row['naselje_mb'],
                'naselje': row['naselje'],
                'ulica_mb': row['ulica_mb'],
                'ulica': row['ulica'],
                'kucni_broj': row['kucni_broj'],
                'geometry': transform(project, wkt.loads(row['geometry'])),
                })

    print('Loading removed addresses')
    old_addresses = []
    with open(os.path.join(rgz_path, 'addresses-removed.csv'), encoding='utf=8') as addresses_old_file:
        reader = csv.DictReader(addresses_old_file)

        for row in reader:
            old_addresses.append({
                'kucni_broj_id': row['kucni_broj_id'],
                'opstina_mb': row['opstina_mb'],
                'opstina': row['opstina'],
                'naselje_mb': row['naselje_mb'],
                'naselje': row['naselje'],
                'ulica_mb': row['ulica_mb'],
                'ulica': row['ulica'],
                'kucni_broj': row['kucni_broj'],
                'geometry': transform(project, wkt.loads(row['geometry'])),
            })

    for i_progress, old_address in enumerate(old_addresses):
        if i_progress % 100 == 0:
            print(f"{i_progress}/{len(old_addresses)}")
        osm_entities_found = get_ref_kucni_broj_from_overpass(overpass_api, old_address['kucni_broj_id'])
        if len(osm_entities_found) == 0:
            # print(f'Skipping {old_address["ulica"]} {old_address["kucni_broj"]} - do not exist in OSM')
            continue

        candidate_new_address = find_in_new_addresses(new_addresses, old_address['ulica'], old_address['kucni_broj'], old_address['geometry'])

        for osm_entity_found in osm_entities_found:
            if osm_entity_found[0] == 'n':
                entity = api.NodeGet(osm_entity_found[1:])
            elif osm_entity_found[0] == 'w':
                entity = api.WayGet(osm_entity_found[1:])
            else:
                entity = api.RelationGet(osm_entity_found[1:])

            if candidate_new_address:
                print(f'{old_address["opstina"]} - {old_address["ulica"]} {old_address["kucni_broj"]} - distance {round(candidate_new_address["geometry"].distance(old_address["geometry"]))}m')
            else:
                print(f'Not found candidate for {old_address["opstina"]} - {old_address["ulica"]} {old_address["kucni_broj"]}')

            # for k in entity['tag']:
            #     print(f'    {k}={entity["tag"][k]}')

            if candidate_new_address:
                entity['tag']['ref:RS:kucni_broj'] = candidate_new_address["kucni_broj_id"]
            else:
                entity['tag']['removed:ref:RS:kucni_broj'] = entity['tag']['ref:RS:kucni_broj']
                note_text = f'Izbrisano iz RGZ-a ' + rgz_last_update
                if 'note' not in entity['tag']:
                    entity['tag']['note'] = note_text
                else:
                    entity['tag']['note'] = entity['tag']['note'] + ';' + note_text
                del entity['tag']['ref:RS:kucni_broj']

            if osm_entity_found[0] == 'n':
                api.NodeUpdate(entity)
            elif osm_entity_found[0] == 'w':
                api.WayUpdate(entity)
            else:
                api.RelationUpdate(entity)

            if candidate_new_address:
                print(f'Updated ref:RS:kucni_broj of {osm_entity_found} from {old_address["kucni_broj_id"]} to {candidate_new_address["kucni_broj_id"]}')
            else:
                print(f'Removed ref:RS:kucni_broj of {osm_entity_found} and adding removed:ref:RS:kucni_broj')
            time.sleep(0.1)

        #time.sleep(0.1)
    api.flush()


def fix_changed(rgz_path, street_mappings):
    api = osmapi.OsmApi(passwordfile='osm-password', changesetauto=True, changesetautosize=100, changesetautotags={
        "comment": f"RGZ address import (updating street and housenumber after cadastre refresh), https://lists.openstreetmap.org/pipermail/imports/2023-March/007187.html",
        "tag": "mechanical=yes",
        "source": "RGZ_AR"
    })
    overpass_api = overpy.Overpass(url='http://localhost:12346/api/interpreter')

    print('Loading changed addresses')
    changed_addresses = []
    with open(os.path.join(rgz_path, 'addresses-changed.csv'), encoding='utf=8') as addresses_changed_file:
        reader = csv.DictReader(addresses_changed_file)

        for row in reader:
            changed_addresses.append({
                'kucni_broj_id': row['kucni_broj_id'],
                'opstina_mb': row['opstina_mb'],
                'opstina': row['opstina'],
                'naselje_old': row['naselje_old'],
                'naselje_new': row['naselje_new'],
                'ulica_old': row['ulica_old'],
                'ulica_new': row['ulica_new'],
                'kucni_broj_old': row['kucni_broj_old'],
                'kucni_broj_new': row['kucni_broj_new'],
                'geometry_old': transform(project, wkt.loads(row['geometry_old'])),
                'geometry_new': transform(project, wkt.loads(row['geometry_new'])),
            })
    for i, changed_address in enumerate(changed_addresses):
        if i % 100 == 0:
            print(f'{i}/{len(changed_addresses)}')
        if changed_address["ulica_old"] == changed_address["ulica_new"] and changed_address["kucni_broj_old"] == changed_address["kucni_broj_new"]:
            # print("Nothing to change")
            continue

        osm_entities_found = get_ref_kucni_broj_from_overpass(overpass_api, changed_address['kucni_broj_id'])
        if len(osm_entities_found) == 0:
            # print(f'Skipping {changed_address["opstina"]} {changed_address["ulica_new"]} {changed_address["kucni_broj_new"]} - do not exist in OSM')
            continue

        for osm_entity_found in osm_entities_found:
            if osm_entity_found[0] == 'n':
                entity = api.NodeGet(osm_entity_found[1:])
            elif osm_entity_found[0] == 'w':
                entity = api.WayGet(osm_entity_found[1:])
            else:
                entity = api.RelationGet(osm_entity_found[1:])

            addrstreet = entity['tag']['addr:street']
            addrhousenumber = entity['tag']['addr:housenumber']
            newstreet = street_mappings[changed_address["ulica_new"]]
            newhousenumber = normalize_name_latin(changed_address["kucni_broj_new"])

            if addrstreet == newstreet and addrhousenumber == newhousenumber:
                print(f"Already fixed ('{changed_address['ulica_old']} {changed_address['kucni_broj_old']}' => '{changed_address['ulica_old']} {changed_address['kucni_broj_new']}')")
                continue
            # for k in entity['tag']:
            #     print(f'    {k}={entity["tag"][k]}')
            print(f"Changing '{addrstreet} {addrhousenumber}' => '{newstreet} {newhousenumber}'")
            response = '' #input()
            if response != '' and response.lower() != 'y' and response.lower() != u'з':
                continue
            entity['tag']['addr:street'] = newstreet
            entity['tag']['addr:housenumber'] = newhousenumber

            if osm_entity_found[0] == 'n':
                api.NodeUpdate(entity)
            elif osm_entity_found[0] == 'w':
                api.WayUpdate(entity)
            else:
                api.RelationUpdate(entity)
            time.sleep(0.1)
    api.flush()


def create_csv_files(rgz_path):
    print('Loading old addresses')
    addresses_old = load_addresses(os.path.join(rgz_path, 'addresses.old.csv'))

    print('Loading new addresses')
    addresses_new = load_addresses(os.path.join(rgz_path, 'addresses.new.csv'))

    print('Detecting new addresses')
    new_addresses = []
    for rgz_kucni_broj_id in addresses_new:
        if rgz_kucni_broj_id not in addresses_old:
            new_addresses.append(addresses_new[rgz_kucni_broj_id])

    with open(os.path.join(rgz_path, 'addresses-added.csv'), 'w', encoding='utf=8') as addresses_added_file:
        writer = csv.DictWriter(
            addresses_added_file, fieldnames=['kucni_broj_id', 'opstina_mb', 'opstina',
                                           'naselje_mb', 'naselje', 'ulica_mb', 'ulica',
                                           'kucni_broj', 'geometry'])
        writer.writeheader()
        for address in new_addresses:
            writer.writerow(address)
    print(f"OK ({len(new_addresses)} new addresses written)")

    print('Detecting removed addresses')
    removed_addresses = []
    for rgz_kucni_broj_id in addresses_old:
        if rgz_kucni_broj_id not in addresses_new:
            removed_addresses.append(addresses_old[rgz_kucni_broj_id])

    with open(os.path.join(rgz_path, 'addresses-removed.csv'), 'w', encoding='utf=8') as addresses_removed_file:
        writer = csv.DictWriter(
            addresses_removed_file, fieldnames=['kucni_broj_id', 'opstina_mb', 'opstina',
                                              'naselje_mb', 'naselje', 'ulica_mb', 'ulica',
                                              'kucni_broj', 'geometry'])
        writer.writeheader()
        for address in removed_addresses:
            writer.writerow(address)
    print(f"OK ({len(removed_addresses)} removed addresses written)")

    print('Detecting changed addresses')
    changed_addresses = []
    for i, rgz_kucni_broj_id in enumerate(addresses_new):
        i = i + 1
        if i % 100000 == 0:
            print(f'{i}/{len(addresses_new)}')
        address_new = addresses_new[rgz_kucni_broj_id]
        if rgz_kucni_broj_id not in addresses_old:
            continue
        address_old = addresses_old[rgz_kucni_broj_id]
        if (address_new['opstina_mb'] != address_old['opstina_mb']) or address_new['opstina'] != address_old['opstina']:
            print(f"Opstina changed for ref:RS:kucni_broj {rgz_kucni_broj_id} from {address_old['opstina']} ({address_old['opstina_mb']}) to {address_new['opstina']} ({address_new['opstina_mb']}), fix manually")
            continue
            #raise Exception('Opstina changed, bailing out')
        naselje_mb_changed = address_new['naselje_mb'] != address_old['naselje_mb']
        naselje_changed = address_new['naselje'] != address_old['naselje']
        ulica_mb_changed = address_new['ulica_mb'] != address_old['ulica_mb']
        ulica_changed = address_new['ulica'] != address_old['ulica']
        kucni_broj_changed = address_new['kucni_broj'] != address_old['kucni_broj']
        geometry_changed = round(address_old['geometry'].distance(address_new['geometry']))

        if naselje_mb_changed or naselje_changed or ulica_mb_changed or ulica_changed or kucni_broj_changed or geometry_changed > 0:
            changed_addresses.append({
                'kucni_broj_id': rgz_kucni_broj_id,
                'opstina_mb': address_new['opstina_mb'],
                'opstina': address_new['opstina'],
                'naselje_mb_old': address_old['naselje_mb'],
                'naselje_mb_new': address_new['naselje_mb'],
                'naselje_mb_changed': naselje_mb_changed,
                'naselje_old': address_old['naselje'],
                'naselje_new': address_new['naselje'],
                'naselje_changed': naselje_changed,
                'ulica_mb_old': address_old['ulica_mb'],
                'ulica_mb_new': address_new['ulica_mb'],
                'ulica_mb_changed': ulica_mb_changed,
                'ulica_old': address_old['ulica'],
                'ulica_new': address_new['ulica'],
                'ulica_changed': ulica_changed,
                'kucni_broj_old': address_old['kucni_broj'],
                'kucni_broj_new': address_new['kucni_broj'],
                'kucni_broj_changed': kucni_broj_changed,
                'geometry_old': address_old['geometry'],
                'geometry_new': address_new['geometry'],
                'geometry_changed': geometry_changed > 0,
                'geometry_changed_meters': geometry_changed
            })

    with open(os.path.join(rgz_path, 'addresses-changed.csv'), 'w', encoding='utf=8') as addresses_changed_file:
        writer = csv.DictWriter(
            addresses_changed_file, fieldnames=[
                'kucni_broj_id', 'opstina_mb', 'opstina',
                'naselje_mb_old', 'naselje_mb_new', 'naselje_mb_changed',
                'naselje_old', 'naselje_new', 'naselje_changed',
                'ulica_mb_old', 'ulica_mb_new', 'ulica_mb_changed',
                'ulica_old', 'ulica_new', 'ulica_changed',
                'kucni_broj_old', 'kucni_broj_new', 'kucni_broj_changed',
                'geometry_old', 'geometry_new', 'geometry_changed', 'geometry_changed_meters'])
        writer.writeheader()
        for address in changed_addresses:
            writer.writerow(address)
    print(f"OK ({len(changed_addresses)} changed addresses written)")


def main():
    parser = argparse.ArgumentParser(
        description='generate_rgz_diff.py - Fix OSM data after RGZ data refresh')
    parser.add_argument('--generate', required=False, help='Should we generate diff files from old and new data', action='store_true')
    parser.add_argument('--fix_deleted_to_added', required=False, help='Should we fix deleted to added addresses - set removed:ref:RS:kucni_broj for those that do not exist anymore and change those that have new ref', action='store_true')
    parser.add_argument('--fix_changed', required=False, help='Should we update addresses for those addresses that are changed', action='store_true')
    parser.add_argument('--rgz_update_date', default=None, required=False, help='Date of RGZ data update, in YYYY-MM-DD format, like 2023-04-23')
    args = parser.parse_args()
    cwd = os.getcwd()
    data_path = os.path.join(cwd, 'data/')
    rgz_path = os.path.join(cwd, 'data/rgz')

    if args.generate:
        create_csv_files(rgz_path)
        return

    if args.fix_deleted_to_added or args.fix_changed:
        print("Loading normalized street names mapping")
        street_mappings = load_mappings(data_path)

    if args.fix_deleted_to_added:
        if args.rgz_update_date is None:
            print("Set --rgz_update_date with date of RGZ data update, in YYYY-MM-DD format, like --rgz_update_date 2023-04-23")
            return
        fix_deleted_to_added(rgz_path, args.rgz_update_date)
    elif args.fix_changed:
        fix_changed(rgz_path, street_mappings)
    else:
        print("Choose either --generate or --fix_deleted_to_added or --fix_changed")


if __name__ == '__main__':
    main()
