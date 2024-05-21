# -*- coding: utf-8 -*-

import csv
import os

from common import CollectRelationWaysHandler, CollectWayNodesHandler, BuildNodesCacheHandler, CollectEntitiesHandler


def main():
    cwd = os.getcwd()
    collect_path = os.path.join(cwd, 'data/osm')
    rgz_path = os.path.join(cwd, 'data/rgz')
    pbf_file = os.path.join(collect_path, 'download/serbia.osm.pbf')
    all_addresses_path = os.path.join(collect_path, 'addresses.csv')

    if os.path.exists(all_addresses_path) and os.path.getsize(all_addresses_path) > 1024 * 1024:
        print("Skipping creation of data/osm/addresses.csv as it already exists")
        return

    crwh = CollectRelationWaysHandler(['addr:street', 'addr:housenumber', 'ref:RS:kucni_broj'])
    crwh.apply_file(pbf_file)
    print(f"Collected all ways ({len(crwh.ways)}) from relations")

    cwnh = CollectWayNodesHandler(crwh.ways, ['addr:street', 'addr:housenumber', 'ref:RS:kucni_broj'])
    cwnh.apply_file(pbf_file)
    print(f"Collected all nodes ({len(cwnh.nodes)}) from ways")

    bnch = BuildNodesCacheHandler(set(cwnh.nodes))
    bnch.apply_file(pbf_file)
    print(f"Found coordinates for all nodes ({len(bnch.nodes_cache)})")

    ceh = CollectEntitiesHandler(bnch.nodes_cache, cwnh.ways_cache, ['addr:street', 'addr:housenumber', 'ref:RS:kucni_broj'])
    ceh.apply_file(pbf_file)
    print(f"Collected all addresses ({len(ceh.entities)})")

    with open(all_addresses_path, 'w', encoding="utf-8") as all_addresses_csv:
        writer = csv.DictWriter(
            all_addresses_csv,
            fieldnames=['osm_id', 'osm_country', 'osm_city', 'osm_postcode', 'osm_street', 'osm_housenumber', 'ref:RS:ulica', 'ref:RS:kucni_broj', 'tags', 'note', 'osm_geometry'])
        writer.writeheader()
        for address in ceh.entities:
            writer.writerow(address)
    print(f"All {len(ceh.entities)} addresses written to data/osm/addresses.csv")


if __name__ == '__main__':
    main()
