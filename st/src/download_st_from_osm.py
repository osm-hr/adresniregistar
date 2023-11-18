# -*- coding: utf-8 -*-

import csv
import os

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
