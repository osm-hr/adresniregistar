# -*- coding: utf-8 -*-

import csv
import os
import sys

import pyproj
from shapely import wkt
from shapely.ops import transform

csv.field_size_limit(sys.maxsize)

wgs84 = pyproj.CRS('EPSG:4326')
utm = pyproj.CRS('EPSG:32634')
project = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True).transform


def load_addresses(addresses_csv_path):
    results = {}
    with open(addresses_csv_path) as addresses_csv_file:
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
                'geometry': row['rgz_geometry'],
            }
    return results


def distance_points(geom1, geom2):
    geom1_obj = transform(project, wkt.loads(geom1))
    geom2_obj = transform(project, wkt.loads(geom2))
    return round(geom1_obj.distance(geom2_obj))


def main():
    cwd = os.getcwd()
    rgz_path = os.path.join(cwd, 'data/rgz')

    print('Loading old addresses')
    addresses_old = load_addresses(os.path.join(rgz_path, 'addresses-old.csv'))

    print('Loading new addresses')
    addresses_new = load_addresses(os.path.join(rgz_path, 'addresses-new.csv'))

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
        if address_new['opstina_mb'] != address_old['opstina_mb']:
            raise Exception('Opstina maticni broj changed, bailing out')
        if address_new['opstina'] != address_old['opstina']:
            raise Exception('Opstina changed, bailing out')
        naselje_mb_changed = address_new['naselje_mb'] != address_old['naselje_mb']
        naselje_changed = address_new['naselje'] != address_old['naselje']
        ulica_mb_changed = address_new['ulica_mb'] != address_old['ulica_mb']
        ulica_changed = address_new['ulica'] != address_old['ulica']
        kucni_broj_changed = address_new['kucni_broj'] != address_old['kucni_broj']
        geometry_changed = distance_points(address_old['geometry'], address_new['geometry'])

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

    with open(os.path.join(rgz_path, 'addresses-changed.csv'), 'w') as addresses_chanfed_file:
        writer = csv.DictWriter(
            addresses_chanfed_file, fieldnames=[
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

    print('Detecting new addresses')
    new_addresses = []
    for rgz_kucni_broj_id in addresses_new:
        if rgz_kucni_broj_id not in addresses_old:
            new_addresses.append(addresses_new[rgz_kucni_broj_id])

    with open(os.path.join(rgz_path, 'addresses-added.csv'), 'w') as addresses_added_file:
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

    with open(os.path.join(rgz_path, 'addresses-removed.csv'), 'w') as addresses_removed_file:
        writer = csv.DictWriter(
            addresses_removed_file, fieldnames=['kucni_broj_id', 'opstina_mb', 'opstina',
                                              'naselje_mb', 'naselje', 'ulica_mb', 'ulica',
                                              'kucni_broj', 'geometry'])
        writer.writeheader()
        for address in removed_addresses:
            writer.writerow(address)
    print(f"OK ({len(removed_addresses)} removed addresses written)")


if __name__ == '__main__':
    main()