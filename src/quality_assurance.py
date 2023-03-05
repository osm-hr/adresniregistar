# -*- coding: utf-8 -*-

import json
import os

import osmium


class CollectRefAddressesHandler(osmium.SimpleHandler):
    """
    Iterates for all addresses with ref:RS:kucni_broj and collect them
    """
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.addresses = {}

    def node(self, n):
        if n.tags.get('ref:RS:kucni_broj'):
            ref = n.tags.get('ref:RS:kucni_broj')
            if ref not in self.addresses:
                self.addresses[ref] = []
            self.addresses[ref].append({
                'id': n.id,
                'type': 'node',
                'tags': {t.k: t.v for t in n.tags}
            })

    def way(self, w):
        if w.tags.get('ref:RS:kucni_broj'):
            ref = w.tags.get('ref:RS:kucni_broj')
            if ref not in self.addresses:
                self.addresses[ref] = []
            self.addresses[ref].append({
                'id': w.id,
                'type': 'way',
                'tags': {t.k: t.v for t in w.tags}
            })

    def relation(self, r):
        if r.tags.get('ref:RS:kucni_broj'):
            ref = r.tags.get('ref:RS:kucni_broj')
            if ref not in self.addresses:
                self.addresses[ref] = []
            self.addresses[ref].append({
                'id': r.id,
                'type': 'relation',
                'tags': {t.k: t.v for t in r.tags}
            })


def find_duplicated_refs(cwd):
    # Finds addresses which have same ref:RS:kucni_broj reference

    osm_path = os.path.join(cwd, 'data/osm')
    pbf_file = os.path.join(osm_path, 'download/serbia.osm.pbf')
    qa_path = os.path.join(cwd, 'data/qa')
    json_file_path = os.path.join(qa_path, 'duplicated_refs.json')
    if os.path.exists(json_file_path):
        print("File data/qa/duplicated_refs.json already exists")
        return

    crah = CollectRefAddressesHandler()
    crah.apply_file(pbf_file)
    print(f"Found all addresses with refs ({len(crah.addresses)} from PBF")

    output_dict = []
    for k, v in crah.addresses.items():
        if len(v) > 1:
            output_dict.append({
                'ref:RS:kucni_broj': k,
                'duplicates': v
            })

    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(output_dict, json_file, ensure_ascii=False)


def main():
    cwd = os.getcwd()
    find_duplicated_refs(cwd)


if __name__ == '__main__':
    main()
