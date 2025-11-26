# -*- coding: utf-8 -*-

import csv
import os
import copy

from common import CollectRelationWaysHandler, CollectWayNodesHandler, BuildNodesCacheHandler, CollectEntitiesHandler


def main():
    cwd = os.getcwd()
    collect_path = os.path.join(cwd, 'data/osm')
    pbf_file = os.path.join(collect_path, 'download/serbia.osm.pbf')
    all_streets_path = os.path.join(collect_path, 'streets.csv')

    if os.path.exists(all_streets_path) and os.path.getsize(all_streets_path) > 1024 * 1024:
        print("Skipping creation of data/osm/streets.csv as it already exists")
        return

    crwh = CollectRelationWaysHandler('highway')
    crwh.apply_file(pbf_file)
    print(f"Collected all ways ({len(crwh.ways)}) from relations")

    cwnh = CollectWayNodesHandler(crwh.ways, 'highway')
    cwnh.apply_file(pbf_file)
    print(f"Collected all nodes ({len(cwnh.nodes)}) from ways")

    bnch = BuildNodesCacheHandler(set(cwnh.nodes))
    bnch.apply_file(pbf_file)
    print(f"Found coordinates for all nodes ({len(bnch.nodes_cache)})")

    ceh = CollectEntitiesHandler(bnch.nodes_cache, cwnh.ways_cache, 'highway', collect_tags=True)
    ceh.apply_file(pbf_file)
    print(f"Collected all streets ({len(ceh.entities)})")

    streets = []
    for e in ceh.entities:
        if e['osm_id'][0] == 'n':
            continue
        if e['osm_geometry'].geom_type not in ('LineString', 'Polygon'):
            print(f'Unknown geometry {e["osm_geometry"].geom_type} with highway tag "{e["tags"]["highway"]}" on OSM entity {e["osm_id"]}')
            continue
        e['ref:RS:ulica'] = e['tags']['ref:RS:ulica'] if 'ref:RS:ulica' in e['tags'] else ''
        e['osm_name'] = e['tags']['name'] if 'name' in e['tags'] else ''
        e['osm_name_sr'] = e['tags']['name:sr'] if 'name:sr' in e['tags'] else ''
        e['osm_name_sr_latn'] = e['tags']['name:sr-Latn'] if 'name:sr-Latn' in e['tags'] else ''
        e['osm_name_en'] = e['tags']['name:en'] if 'name:en' in e['tags'] else ''
        e['osm_alt_name'] = e['tags']['alt_name'] if 'alt_name' in e['tags'] else ''
        e['osm_alt_name_sr'] = e['tags']['alt_name:sr'] if 'alt_name:sr' in e['tags'] else ''
        e['osm_alt_name_sr_latn'] = e['tags']['alt_name:sr-Latn'] if 'alt_name:sr-Latn' in e['tags'] else ''
        e['osm_short_name'] = e['tags']['short_name'] if 'short_name' in e['tags'] else ''
        e['osm_short_name_sr'] = e['tags']['short_name:sr'] if 'short_name:sr' in e['tags'] else ''
        e['osm_short_name_sr_latn'] = e['tags']['short_name:sr-Latn'] if 'short_name:sr-Latn' in e['tags'] else ''
        e['osm_int_name'] = e['tags']['int_name'] if 'int_name' in e['tags'] else ''
        del e['osm_country']
        del e['osm_city']
        del e['osm_postcode']
        del e['osm_street']
        del e['osm_housenumber']
        del e['ref:RS:kucni_broj']

        if ';' in e['ref:RS:ulica']:
            all_refs = e['ref:RS:ulica'].split(';')
            for ref in all_refs:
                temp_e = copy.deepcopy(e)
                temp_e['ref:RS:ulica'] = ref
                streets.append(temp_e)
            continue

        if 'ref:RS:ulica:left' in e['tags'] and 'ref:RS:ulica:right' in e['tags'] and e['tags']['ref:RS:ulica:left'] == e['tags']['ref:RS:ulica:right']:
            print(f'Same value in both "ref:RS:ulica:left" and "ref:RS:ulica:right" for OSM entity {e["osm_id"]}')
            continue

        if 'ref:RS:ulica:left' in e['tags']:
            e2 = copy.deepcopy(e)
            e2['ref:RS:ulica'] = e2['tags']['ref:RS:ulica:left']
            e2['osm_name'] = e2['tags']['name:left'] if 'name:left' in e2['tags'] else (e2['tags']['name'] if 'name' in e2['tags'] else '')
            e2['osm_name_sr'] = e2['tags']['name:left:sr'] if 'name:left:sr' in e['tags'] else (e2['tags']['name:sr'] if 'name:sr' in e2['tags'] else '')
            e2['osm_name_sr_latn'] = e2['tags']['name:left:sr-Latn'] if 'name:left:sr-Latn' in e2['tags'] else (e2['tags']['name:sr-Latn'] if 'name:sr-Latn' in e2['tags'] else '')
            e2['osm_name_en'] = e2['tags']['name:left:en'] if 'name:left:en' in e2['tags'] else (e2['tags']['name:en'] if 'name:en' in e2['tags'] else '')
            e2['osm_alt_name'] = e2['tags']['alt_name:left'] if 'alt_name:left' in e2['tags'] else (e['tags']['alt_name'] if 'alt_name' in e2['tags'] else '')
            e2['osm_alt_name_sr'] = e2['tags']['alt_name:left:sr'] if 'alt_name:left:sr' in e['tags'] else (e2['tags']['alt_name:sr'] if 'alt_name:sr' in e2['tags'] else '')
            e2['osm_alt_name_sr_latn'] = e2['tags']['alt_name:left:sr-Latn'] if 'alt_name:left:sr-Latn' in e2['tags'] else (e2['tags']['alt_name:sr-Latn'] if 'alt_name:sr-Latn' in e2['tags'] else '')
            e2['osm_short_name'] = e2['tags']['short_name:left'] if 'short_name:left' in e2['tags'] else (e2['tags']['short_name'] if 'short_name' in e2['tags'] else '')
            e2['osm_short_name_sr'] = e2['tags']['short_name:left:sr'] if 'short_name:left:sr' in e2['tags'] else (e2['tags']['short_name:sr'] if 'short_name:sr' in e2['tags'] else '')
            e2['osm_short_name_sr_latn'] = e2['tags']['short_name:left:sr-Latn'] if 'short_name:left:sr-Latn' in e2['tags'] else (e2['tags']['short_name:sr-Latn'] if 'short_name:sr-Latn' in e2['tags'] else '')
            e2['osm_int_name'] = e2['tags']['int_name:left'] if 'int_name:left' in e2['tags'] else (e2['tags']['int_name'] if 'int_name' in e2['tags'] else '')
            streets.append(e2)

        if 'ref:RS:ulica:right' in e['tags']:
            e2 = copy.deepcopy(e)
            e2['ref:RS:ulica'] = e2['tags']['ref:RS:ulica:right']
            e2['osm_name'] = e2['tags']['name:right'] if 'name:right' in e2['tags'] else (e2['tags']['name'] if 'name' in e2['tags'] else '')
            e2['osm_name_sr'] = e2['tags']['name:right:sr'] if 'name:right:sr' in e2['tags'] else (e2['tags']['name:sr'] if 'name:sr' in e2['tags'] else '')
            e2['osm_name_sr_latn'] = e2['tags']['name:right:sr-Latn'] if 'name:right:sr-Latn' in e2['tags'] else (e2['tags']['name:sr-Latn'] if 'name:sr-Latn' in e2['tags'] else '')
            e2['osm_name_en'] = e2['tags']['name:right:en'] if 'name:right:en' in e2['tags'] else (e2['tags']['name:en'] if 'name:en' in e2['tags'] else '')
            e2['osm_alt_name'] = e2['tags']['alt_name:right'] if 'alt_name:right' in e2['tags'] else (e2['tags']['alt_name'] if 'alt_name' in e2['tags'] else '')
            e2['osm_alt_name_sr'] = e2['tags']['alt_name:right:sr'] if 'alt_name:right:sr' in e2['tags'] else (e2['tags']['alt_name:sr'] if 'alt_name:sr' in e2['tags'] else '')
            e2['osm_alt_name_sr_latn'] = e2['tags']['alt_name:right:sr-Latn'] if 'alt_name:right:sr-Latn' in e2['tags'] else (e2['tags']['alt_name:sr-Latn'] if 'alt_name:sr-Latn' in e2['tags'] else '')
            e2['osm_short_name'] = e2['tags']['short_name:right'] if 'short_name:right' in e2['tags'] else (e2['tags']['short_name'] if 'short_name' in e2['tags'] else '')
            e2['osm_short_name_sr'] = e2['tags']['short_name:right:sr'] if 'short_name:right:sr' in e2['tags'] else (e2['tags']['short_name:sr'] if 'short_name:sr' in e2['tags'] else '')
            e2['osm_short_name_sr_latn'] = e2['tags']['short_name:right:sr-Latn'] if 'short_name:right:sr-Latn' in e2['tags'] else (e2['tags']['short_name:sr-Latn'] if 'short_name:sr-Latn' in e2['tags'] else '')
            e2['osm_int_name'] = e2['tags']['int_name:right'] if 'int_name:right' in e2['tags'] else (e2['tags']['int_name'] if 'int_name' in e2['tags'] else '')
            streets.append(e2)

        if 'ref:RS:ulica:left' not in e['tags'] and 'ref:RS:ulica:right' not in e['tags']:
            streets.append(e)

    with open(all_streets_path, 'w', encoding="utf-8") as all_streets_csv:
        writer = csv.DictWriter(
            all_streets_csv,
            fieldnames=['osm_id', 'osm_name', 'osm_name_sr', 'osm_name_sr_latn', 'osm_name_en',
                        'osm_alt_name', 'osm_alt_name_sr', 'osm_alt_name_sr_latn',
                        'osm_short_name', 'osm_short_name_sr', 'osm_short_name_sr_latn',
                        'osm_int_name', 'ref:RS:ulica', 'note', 'tags', 'osm_geometry'])
        writer.writeheader()
        for address in streets:
            writer.writerow(address)
    print(f"All {len(streets)} streets written to data/osm/streets.csv")


if __name__ == '__main__':
    main()
