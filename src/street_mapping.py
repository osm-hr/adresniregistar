# -*- coding: utf-8 -*-

import csv
import os
import pandas as pd

import osmium
from common import normalize_name

#csv.field_size_limit(sys.maxsize)


class CollectRgzRefMappingHandler(osmium.SimpleHandler):
    """
    Iterates for all ways and creates mapping ref:RS:ulica -> name
    """
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.mappings = {}

    def way(self, w):
        if w.tags.get('ref:RS:ulica') and w.tags.get("highway") and w.tags.get("name"):
            ref = w.tags.get("ref:RS:ulica")
            name = w.tags.get("name")
            if ref not in self.mappings:
                self.mappings[ref] = set()
            self.mappings[ref].add(name)


class CollectOsmMappingsHandler(osmium.SimpleHandler):
    """
    Iterates for all ways and creates mapping "normalized name" -> Name
    """
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.mappings = {}

    def way(self, w):
        if w.tags.get("highway") and w.tags.get("name"):
            name = w.tags.get("name")
            normalized_name = normalize_name(name)

            if normalized_name not in self.mappings:
                self.mappings[normalized_name] = set()
            self.mappings[normalized_name].add(name)


def load_curated(cwd):
    curated_street_csv_path = os.path.join(cwd, 'curated_streets.csv')
    curated_street = {}

    with open(curated_street_csv_path, encoding="utf-8") as curated_street_csv_file:
        reader = csv.DictReader(curated_street_csv_file)
        for row in reader:
            rgz_name = row['rgz_name']
            name = row['name']
            curated_street[rgz_name] = name
    return curated_street


def load_ref_mapping(cwd):
    osm_path = os.path.join(cwd, 'data/osm')
    pbf_file = os.path.join(osm_path, 'download/serbia.osm.pbf')

    crrmh = CollectRgzRefMappingHandler()
    crrmh.apply_file(pbf_file)
    return crrmh.mappings


def load_osm_mappings(cwd):
    osm_path = os.path.join(cwd, 'data/osm')
    pbf_file = os.path.join(osm_path, 'download/serbia.osm.pbf')

    comh = CollectOsmMappingsHandler()
    comh.apply_file(pbf_file)
    return comh.mappings


def convert_rgz_name_to_osm_name(rgz_id, rgz_name, curated_streets, ref_mappings, osm_mappings):
    if rgz_name in curated_streets:
        return curated_streets[rgz_name]
    if rgz_id in ref_mappings:
        if len(ref_mappings[rgz_id]) == 1:
        return list(ref_mappings[rgz_id])[0]
    normalized_name = normalize_name(rgz_name)
    if normalized_name in osm_mappings:
        if len(osm_mappings[normalized_name]) == 1:
            return list(osm_mappings[normalized_name])[0]
        else:
            pass
    return None


def process_opstina(opstina, data_path, curated_streets, ref_mappings, osm_mappings):
    input_rgz_file = os.path.join(data_path, f'rgz/csv/{opstina}.csv')
    df_rgz = pd.read_csv(input_rgz_file)
    all_streets = df_rgz[['rgz_ulica_mb', 'rgz_ulica']].drop_duplicates()
    mapping = {}
    for _, street in all_streets.iterrows():
        rgz_id = str(street['rgz_ulica_mb'])
        rgz_ulica = street['rgz_ulica']
        if rgz_ulica not in mapping:
            mapping[rgz_ulica] = set()
        converted_name = convert_rgz_name_to_osm_name(rgz_id, rgz_ulica, curated_streets, ref_mappings, osm_mappings)
        if converted_name:
            mapping[rgz_ulica].add(converted_name)


def main():
    """
    Here we denote "Name" as normal street name, "NAME" as RGZ name (capitalized) and "nname" as normalized name,
    We need to create mapping "NAME"->"Name".
    From OSM, we can get 2 mappings:
    1. "ref:RS:ulica" -> list("Name)
    2. "nname" -> list("Name")

    Then, for each "NAME" street in RGZ:
    * we try to find it in special, human mapped list (part of source code)
    * if not, we check if there is "ref:RS:ulica" mapping to Name
      If there is and there is only one mapping, we use it. If there are multiple mappings, we use Levenstein distance to pick best guess.
    * If not, we calculate "NAME"->"nname". Then we try to find "Name" that matches that normalized name.
      If there is only one, we use it. If there are multiple names, we cannot pick any particular.
    * If we cannot find it from curated list, nor "ref:RS:ulica" nor OSM, we guess it by making only first letter capital and add more rules
    ** If streets ends with latin number, we capitalize that
    ** If some words ends with "ић" or "ића", we capitalize that word

    """
    cwd = os.getcwd()
    curated_streets = load_curated(cwd)
    print(f"Collected all curated ({len(curated_streets)}) mappings")

    ref_mappings = load_ref_mapping(cwd)
    print(f"Collected all ref:RS:ulica ({len(ref_mappings)}) mappings")

    osm_mappings = load_osm_mappings(cwd)
    print(f"Collected all OSM ({len(osm_mappings)}) mappings")

    data_path = os.path.join(cwd, 'data/')
    rgz_csv_path = os.path.join(data_path, 'rgz/csv')
    rgz_mapping_path = os.path.join(data_path, 'rgz/mapping')

    total_csvs = len(os.listdir(rgz_csv_path))
    for i, file in enumerate(os.listdir(rgz_csv_path)):
        if not file.endswith(".csv"):
            continue
        opstina = file[:-4]
        print(f"{i + 1}/{total_csvs} Processing {opstina}")
        process_opstina(opstina, data_path, curated_streets, ref_mappings, osm_mappings)


if __name__ == '__main__':
    main()
