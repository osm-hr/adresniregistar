# -*- coding: utf-8 -*-

import argparse
import csv
import os
import sys
import time

import osmapi
import overpy
import pyproj
from requests_oauthlib import OAuth2Session
from shapely import wkt
from shapely.ops import transform

from common import cyr2lat, cyr2intname, token_loader, save_and_get_access_token
from street_mapping import StreetMapping

csv.field_size_limit(sys.maxsize)

wgs84 = pyproj.CRS('EPSG:4326')
utm = pyproj.CRS('EPSG:32634')
project = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True).transform
inverse_project = pyproj.Transformer.from_crs(utm, wgs84, always_xy=True).transform


def load_streets(streets_csv_path):
    results = {}
    with open(streets_csv_path, encoding='utf=8') as streets_csv_file:
        reader = csv.DictReader(streets_csv_file)

        for row in reader:
            results[row['rgz_ulica_mb']] = {
                'opstina_mb': row['rgz_opstina_mb'],
                'opstina': row['rgz_opstina'],
                'naselje_mb': row['rgz_naselje_mb'],
                'naselje': row['rgz_naselje'],
                'ulica_mb': row['rgz_ulica_mb'],
                'ulica': row['rgz_ulica'],
                'geometry': transform(project, wkt.loads(row['rgz_geometry'])),
            }
    return results


def get_ref_ulica_from_overpass(overpass_api, rgz_ulica_mb):
    response = overpass_api.query(f"""
        [out:json];
        (
          nwr["ref:RS:ulica"="{rgz_ulica_mb}"];
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


def fix_deleted(rgz_path):
    """
    Nalazi obrisane ulice i briše im ref:RS:ulica tag
    """
    api = osmapi.OsmApi(passwordfile='osm-password', changesetauto=True, changesetautosize=100, changesetautotags={
        "comment": f"RGZ street import (removing ref:RS:ulica after cadastre refresh), https://lists.openstreetmap.org/pipermail/imports/2023-March/007187.html",
        "tag": "mechanical=yes",
        "source": "RGZ_ST"
    })
    overpass_api = overpy.Overpass(url='http://localhost:12346/api/interpreter')

    print('Loading removed streets')
    old_streets = []
    with open(os.path.join(rgz_path, 'streets-removed.csv'), encoding='utf=8') as streets_old_file:
        reader = csv.DictReader(streets_old_file)

        for row in reader:
            old_streets.append({
                'opstina_mb': row['opstina_mb'],
                'opstina': row['opstina'],
                'naselje_mb': row['naselje_mb'],
                'naselje': row['naselje'],
                'ulica_mb': row['ulica_mb'],
                'ulica': row['ulica'],
                'geometry': transform(project, wkt.loads(row['geometry'])),
            })

    for i_progress, old_street in enumerate(old_streets):
        if i_progress % 100 == 0:
            print(f"{i_progress}/{len(old_streets)}")
        osm_entities_found = get_ref_ulica_from_overpass(overpass_api, old_street['ulica_mb'])
        if len(osm_entities_found) == 0:
            print(f'Skipping {old_street["ulica"]} ({old_street["ulica_mb"]}) - do not exist in OSM')
            continue

        for osm_entity_found in osm_entities_found:
            if osm_entity_found[0] == 'n':
                entity = api.NodeGet(osm_entity_found[1:])
            elif osm_entity_found[0] == 'w':
                entity = api.WayGet(osm_entity_found[1:])
            else:
                entity = api.RelationGet(osm_entity_found[1:])

            entity['tag']['removed:ref:RS:ulica'] = entity['tag']['ref:RS:ulica']
            del entity['tag']['ref:RS:ulica']

            if osm_entity_found[0] == 'n':
                api.NodeUpdate(entity)
            elif osm_entity_found[0] == 'w':
                api.WayUpdate(entity)
            else:
                api.RelationUpdate(entity)

            print(f'Removed ref:RS:ulica of {osm_entity_found} and added removed:ref:RS:ulica')
            time.sleep(1)

        time.sleep(1)
    api.flush()


def rename_changed(cwd, rgz_path, oauth_session):
    street_mappings = StreetMapping(os.path.join(cwd, '..', 'ar'))

    api = osmapi.OsmApi(session=oauth_session)
    api.ChangesetCreate({
        "comment": f"RGZ street renaming (after cadastre refresh), https://lists.openstreetmap.org/pipermail/imports/2023-March/007187.html",
        "tag": "mechanical=yes",
        "source": "RGZ_AR"
    })
    changeset_count = 0

    overpass_api = overpy.Overpass(url='http://localhost:12345/api/interpreter')

    print('Loading changed streets')
    changed_streets = []
    with open(os.path.join(rgz_path, 'streets-changed.csv'), encoding='utf=8') as streets_changed_file:
        reader = csv.DictReader(streets_changed_file)

        for row in reader:
            if not row['ulica_changed']:
                #print(f"    Geometry of street {row['ulica_old']} not changed, skipping")
                continue

            old_name = street_mappings.get_name(row['ulica_old'], str(row['ulica_mb']))
            new_name = street_mappings.get_name(row['ulica_new'], str(row['ulica_mb']))
            if old_name == new_name:
                #print(f"Skipping renaming street {row['ulica_old']}->{row['ulica_new']} ({row['ulica_mb']}) as name didn't change after mapping (still {old_name})")
                continue

            changed_streets.append({
                'opstina_mb': row['opstina_mb'],
                'opstina': row['opstina'],
                'naselje_mb': row['naselje_mb_new'],
                'naselje': row['naselje_new'],
                'ulica_mb': row['ulica_mb'],
                'ulica_changed': row['ulica_changed'],
                'rgz_ulica_old': row['ulica_old'],
                'rgz_ulica_new': row['ulica_new'],
                'old_name': old_name,
                'new_name': new_name
            })

    for i_progress, changed_street in enumerate(changed_streets):
        print(f"{i_progress}/{len(changed_streets)}")

        osm_entities_found = get_ref_ulica_from_overpass(overpass_api, changed_street['ulica_mb'])
        if len(osm_entities_found) == 0:
            print(f'Skipping {changed_street["rgz_ulica_old"]} ({changed_street["ulica_mb"]}) - do not exist in OSM')
            continue

        old_name = changed_street['old_name']
        new_name = changed_street['new_name']

        move_to_old_name = None

        for osm_entity_found in osm_entities_found:
            if osm_entity_found[0] == 'n':
                entity = api.NodeGet(osm_entity_found[1:])
            elif osm_entity_found[0] == 'w':
                entity = api.WayGet(osm_entity_found[1:])
            else:
                entity = api.RelationGet(osm_entity_found[1:])

            need_change = False
            if entity['tag']['name'] != new_name:
                need_change = True

            if not need_change:
                print(f'Skipping {changed_street["new_name"]} ({changed_street["ulica_mb"]}) - already renamed')
                continue

            if move_to_old_name is None:
                print(f"Changing '{old_name}' => '{new_name}' for street {changed_street['rgz_ulica_old']} ({changed_street['ulica_mb']}). Move name to old_name (Y/n)?")
                move_to_old_name = True
                response = input()
                if response.lower() == 'n' or response.lower() == u'н':
                    move_to_old_name = False

            entity['tag']['name'] = new_name
            entity['tag']['name:sr'] = new_name
            entity['tag']['name:sr-Latn'] = cyr2lat(new_name)
            entity['tag']['int_name'] = cyr2intname(new_name)
            if 'alt_name' in entity['tag']: del entity['tag']['alt_name']
            if 'alt_name:sr' in entity['tag']: del entity['tag']['alt_name:sr']
            if 'alt_name:sr-Latn' in entity['tag']: del entity['tag']['alt_name:sr-Latn']
            if 'short_name' in entity['tag']: del entity['tag']['short_name']
            if 'short_name:sr' in entity['tag']: del entity['tag']['short_name:sr']
            if 'short_name:sr-Latn' in entity['tag']: del entity['tag']['short_name:sr-Latn']

            if move_to_old_name:
                entity['tag']['old_name'] = old_name
                entity['tag']['old_name:sr'] = old_name
                entity['tag']['old_name:sr-Latn'] = cyr2lat(old_name)

            if osm_entity_found[0] == 'n':
                api.NodeUpdate(entity)
            elif osm_entity_found[0] == 'w':
                api.WayUpdate(entity)
            else:
                api.RelationUpdate(entity)
            changeset_count = changeset_count + 1

            print(f'Changed {changed_street["rgz_ulica_old"]}=>{changed_street['rgz_ulica_new']} ({changed_street["ulica_mb"]})')

            if changeset_count % 2000 == 0:
                api.ChangesetClose()
                time.sleep(5)
                api.ChangesetCreate({
                    "comment": f"RGZ street renaming (after cadastre refresh), https://lists.openstreetmap.org/pipermail/imports/2023-March/007187.html",
                    "tag": "mechanical=yes",
                    "source": "RGZ_AR"
                })
            time.sleep(1)


        time.sleep(1)
    api.ChangesetClose()


def create_csv_files(rgz_path):
    print('Loading old streets')
    streets_old = load_streets(os.path.join(rgz_path, 'streets.old.csv'))

    print('Loading new streets')
    streets_new = load_streets(os.path.join(rgz_path, 'streets.new.csv'))

    print('Detecting new streets')
    new_streets = []
    for rgz_ulica_mb_id in streets_new:
        if rgz_ulica_mb_id not in streets_old:
            new_streets.append(streets_new[rgz_ulica_mb_id])

    with open(os.path.join(rgz_path, 'streets-added.csv'), 'w', encoding='utf=8') as streets_added_file:
        writer = csv.DictWriter(
            streets_added_file, fieldnames=['opstina_mb', 'opstina', 'naselje_mb', 'naselje', 'ulica_mb', 'ulica', 'geometry'])
        writer.writeheader()
        for street in new_streets:
            writer.writerow(street)
    print(f"OK ({len(new_streets)} new streets written)")

    print('Detecting removed streets')
    removed_streets = []
    for rgz_ulica_mb_id in streets_old:
        if rgz_ulica_mb_id not in streets_new:
            removed_streets.append(streets_old[rgz_ulica_mb_id])

    with open(os.path.join(rgz_path, 'streets-removed.csv'), 'w', encoding='utf=8') as streets_removed_file:
        writer = csv.DictWriter(
            streets_removed_file, fieldnames=['opstina_mb', 'opstina', 'naselje_mb', 'naselje', 'ulica_mb', 'ulica', 'geometry'])
        writer.writeheader()
        for street in removed_streets:
            writer.writerow(street)
    print(f"OK ({len(removed_streets)} removed streets written)")

    print('Detecting changed streets')
    changed_streets = []
    for i, rgz_ulica_mb_id in enumerate(streets_new):
        i = i + 1
        if i % 10000 == 0:
            print(f'{i}/{len(streets_new)}')
        street_new = streets_new[rgz_ulica_mb_id]
        if rgz_ulica_mb_id not in streets_old:
            continue
        street_old = streets_old[rgz_ulica_mb_id]
        if (street_new['opstina_mb'] != street_old['opstina_mb']) or street_new['opstina'] != street_old['opstina']:
            print(f"Opstina changed for ref:RS:ulica {rgz_ulica_mb_id} from {street_old['opstina']} ({street_old['opstina_mb']}) to {street_new['opstina']} ({street_new['opstina_mb']}), fix manually")
            continue
            #raise Exception('Opstina changed, bailing out')
        naselje_mb_changed = street_new['naselje_mb'] != street_old['naselje_mb']
        naselje_changed = street_new['naselje'] != street_old['naselje']
        ulica_changed = street_new['ulica'] != street_old['ulica']
        geometry_changed = round(street_old['geometry'].hausdorff_distance(street_new['geometry']))

        if naselje_mb_changed or naselje_changed or ulica_changed or geometry_changed > 0:
            changed_streets.append({
                'opstina_mb': street_new['opstina_mb'],
                'opstina': street_new['opstina'],
                'naselje_mb_old': street_old['naselje_mb'],
                'naselje_mb_new': street_new['naselje_mb'],
                'naselje_mb_changed': naselje_mb_changed,
                'naselje_old': street_old['naselje'],
                'naselje_new': street_new['naselje'],
                'naselje_changed': naselje_changed,
                'ulica_mb': rgz_ulica_mb_id,
                'ulica_old': street_old['ulica'],
                'ulica_new': street_new['ulica'],
                'ulica_changed': ulica_changed,
                'geometry_old': street_old['geometry'],
                'geometry_new': street_new['geometry'],
                'geometry_changed': geometry_changed > 0,
                'geometry_changed_meters': geometry_changed
            })

    with open(os.path.join(rgz_path, 'streets-changed.csv'), 'w', encoding='utf=8') as streets_changed_file:
        writer = csv.DictWriter(streets_changed_file, fieldnames=[
            'opstina_mb', 'opstina',
            'naselje_mb_old', 'naselje_mb_new', 'naselje_mb_changed',
            'naselje_old', 'naselje_new', 'naselje_changed', 'ulica_mb',
            'ulica_old', 'ulica_new', 'ulica_changed',
            'geometry_old', 'geometry_new', 'geometry_changed', 'geometry_changed_meters'])
        writer.writeheader()
        for street in changed_streets:
            writer.writerow(street)
    print(f"OK ({len(changed_streets)} changed streets written)")


def main():
    parser = argparse.ArgumentParser(
        description='generate_rgz_diff.py - Fix OSM data after RGZ data refresh')
    parser.add_argument('--generate', required=False, help='Should we generate diff files from old and new data', action='store_true')
    parser.add_argument('--fix_deleted', required=False, help='Should we fix deleted streets - set removed:ref:RS:ulica for those that do not exist anymore', action='store_true')
    parser.add_argument('--rename-changed', required=False, help='Should we rename deleted streets - move name to old_name and rename street', action='store_true')
    args = parser.parse_args()
    cwd = os.getcwd()
    rgz_path = os.path.join(cwd, 'data/rgz')

    if args.generate:
        create_csv_files(rgz_path)
        return

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

    if args.fix_deleted:
        fix_deleted(rgz_path)
        return

    if args.rename_changed:
        rename_changed(cwd, rgz_path, oauth_session)
        return

    print("Choose either --generate, --fix_deleted or --rename-changed")


if __name__ == '__main__':
    main()
