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
            'naselje_old', 'naselje_new', 'naselje_changed',
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
    args = parser.parse_args()
    cwd = os.getcwd()
    rgz_path = os.path.join(cwd, 'data/rgz')

    if args.generate:
        create_csv_files(rgz_path)
        return

    if args.fix_deleted:
        fix_deleted(rgz_path)
        return

    print("Choose either --generate or --fix_deleted")


if __name__ == '__main__':
    main()
