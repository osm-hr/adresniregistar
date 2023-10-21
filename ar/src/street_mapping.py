# -*- coding: utf-8 -*-

import sys
import csv
import os
import pandas as pd

import osmium
from common import normalize_name_latin


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
                self.mappings[ref] = []
            found = False
            for entry in self.mappings[ref]:
                if name == entry['name']:
                    found = True
                    entry['refs'].append('w' + str(w.id))
                    break
            if not found:
                self.mappings[ref].append({'name': name, 'refs': ['w' + str(w.id)]})


class CollectOsmMappingsHandler(osmium.SimpleHandler):
    """
    Iterates for all ways and creates mapping "normalized latin name" -> Name
    """
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.mappings = {}

    def way(self, w):
        if w.tags.get("highway") and w.tags.get("name"):
            name = w.tags.get("name")
            if 'a' in name or 'e' in name or 'i' in name or 'o' in name or 'u' in name:
                # This name is not cyrillic, just ignore
                return

            normalized_name = normalize_name_latin(name)
            if normalized_name not in self.mappings:
                self.mappings[normalized_name] = []
            found = False
            for entry in self.mappings[normalized_name]:
                if name == entry['name']:
                    found = True
                    entry['refs'].append('w' + str(w.id))
                    break
            if not found:
                self.mappings[normalized_name].append({'name': name, 'refs': ['w' + str(w.id)]})


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


def best_effort_decapitalize(name):
    name = name.title()
    if '.' in name and '. ' not in name and name[0:name.find('.')].isnumeric():
        name = name[:name.find('.') + 1] + ' ' + name[name.find('.') + 1:]

    # Ћирила И Методија, Пут За Љиг, Заселак Код Крста
    name = name.replace(" И ", " и ").replace(" За ", " за ").replace(" Код ", " код ")

    words_to_replace = [" Баре", " Битке", " Бораца", " Брдо", " Брег", " Бригада", " Бригаде", " Бунара",
                        " Венац", " Вијенац", " Воде",
                        " Гај",
                        " Дивизија", " Дивизије", " До", " Дом", " Други", " Друга", " Друм",
                        " Језеро", " Јунака",
                        " Засеок", " Зона",
                        " Камен", " Каплара", " Комуне", " Коса", " Крај", " Крш", " Крша",
                        " Лад", " Лаз",
                        " Насеље", " Нова",
                        " Њива",
                        " Плато", " Поље", " Поток", " Прва", " Први", " Пруга", " Пруге", " Пука", " Пут",
                        " Раван", " Ратника", " Револуције", " Реке", " Река",
                        " Салаш", " Салаша", " Сокак", " Сокаче", " Стена",
                        " Улица",
                        " Фронта",
                        " Јануар", " Јануара", " Фебруар", " Фебруара", " Март", " Марта", " Април", " Априла", " Мај",
                        " Маја", " Јун", " Јуна", " Јул", " Јула", " Август", " Августа", " Септембар", " Септембра",
                        " Октобар", " Октобра", " Новембар", " Новембра", " Децембар", " Децембра"]

    for word in words_to_replace:
        if not word.startswith(" "):
            raise Exception(f"Word to replace must start with space and word '{word}' doesn't")
        if not word[1].isupper():
            raise Exception(f"Word to replace must start with capital case and word '{word}' doesn't")
        name = name.replace(word + " ", word.lower() + " ")
        if name.endswith(word):
            name = name[:len(name) - len(word)] + word.lower()

    return name


def convert_rgz_name_to_osm_name(rgz_id, rgz_name, curated_streets, ref_mappings, osm_mappings):
    rgz_name = rgz_name.rstrip().replace('    ', ' ').replace('   ', ' ').replace('  ', ' ')
    # Find first in curated list
    if rgz_name in curated_streets:
        return curated_streets[rgz_name], 'curated', ''

    # Find in ref:RS:ulica mappings next
    if rgz_id in ref_mappings:
        if len(ref_mappings[rgz_id]) == 1:
            return ref_mappings[rgz_id][0]['name'], 'ref:RS:ulica', ','.join(ref_mappings[rgz_id][0]['refs'])

    # Find from latin normalized name
    normalized_name = normalize_name_latin(rgz_name)
    if normalized_name in osm_mappings:
        if len(osm_mappings[normalized_name]) == 1:
            return osm_mappings[normalized_name][0]['name'], 'OSM', ','.join(osm_mappings[normalized_name][0]['refs'])

    best_effort = best_effort_decapitalize(rgz_name)
    return best_effort, 'BestEffort', ''


def process_opstina(mapping, opstina, data_path, curated_streets, ref_mappings, osm_mappings):
    input_rgz_file = os.path.join(data_path, f'rgz/csv/{opstina}.csv')
    df_rgz = pd.read_csv(input_rgz_file)
    all_streets = df_rgz[['rgz_ulica_mb', 'rgz_ulica']].drop_duplicates()

    for _, street in all_streets.iterrows():
        rgz_id = str(street['rgz_ulica_mb'])
        rgz_ulica = street['rgz_ulica']
        if rgz_ulica in mapping:
            continue
        converted_name, source, refs = convert_rgz_name_to_osm_name(rgz_id, rgz_ulica, curated_streets, ref_mappings, osm_mappings)
        if converted_name:
            mapping[rgz_ulica] = ({'name': converted_name, 'source': source, 'refs': refs})


def main():
    """
    Here we denote "Name" as normal street name, "NAME" as RGZ name (capitalized) and "nname" as normalized name,
    We need to create mapping "NAME"->"Name".
    From OSM, we can get 3 mappings:
    1. "ref:RS:ulica" -> list("Name)
    2. "nname (latin)" -> list("Name")
    3. "nname (ascii)" -> list("Name")

    Then, for each "NAME" street in RGZ:
    * we try to find it in special, human mapped list (part of source code)
    * if not, we check if there is "ref:RS:ulica" mapping to Name
      If there is and there is only one mapping, we use it. If there are multiple mappings, we ignore it.
    * If not, we calculate "NAME"->"nname (latin)". Then we try to find "Name" that matches that normalized name.
      If there is only one, we use it. If there are multiple names, we cannot pick any particular.
    * If we cannot find it from curated list, nor "ref:RS:ulica" nor OSM, we guess it by making only first letter capital and adding more rules
    ** If streets ends with latin number, we capitalize that
    ** If some words ends with "ић" or "ића", we capitalize that word
    """
    cwd = os.getcwd()
    data_path = os.path.join(cwd, 'data/')
    rgz_csv_path = os.path.join(data_path, 'rgz/csv')
    mapping_csv_path = os.path.join(data_path, "mapping/mapping.csv")

    if os.path.exists(mapping_csv_path):
        print("Skipping mapping generation, file data/mapping/mapping.csv already exist")
        return

    curated_streets = load_curated(cwd)
    print(f"Collected all curated ({len(curated_streets)}) mappings")

    ref_mappings = load_ref_mapping(cwd)
    print(f"Collected all ref:RS:ulica ({len(ref_mappings)}) mappings")

    osm_mappings = load_osm_mappings(cwd)
    print(f"Collected all OSM ({len(osm_mappings)}) mappings")

    total_csvs = len(os.listdir(rgz_csv_path))
    mapping = {}
    for i, file in enumerate(os.listdir(rgz_csv_path)):
        if not file.endswith(".csv"):
            continue
        opstina = file[:-4]
        print(f"{i + 1}/{total_csvs} Processing {opstina}")
        process_opstina(mapping, opstina, data_path, curated_streets, ref_mappings, osm_mappings)

    with open(mapping_csv_path, 'w', encoding="utf-8") as mapping_csv:
        writer = csv.DictWriter(
            mapping_csv,
            fieldnames=['rgz_name', 'name', 'source', 'refs'])
        writer.writeheader()
        sorted_keys = sorted(mapping.keys())
        for rgz_name in sorted_keys:
            writer.writerow({
                'rgz_name': rgz_name,
                'name': mapping[rgz_name]['name'],
                'source': mapping[rgz_name]['source'],
                'refs': mapping[rgz_name]['refs'],
            })
    print(f"All {len(mapping)} mappings written to data/mapping/mapping.csv")


def fix_framacalc():
    framacalc_csv = []
    with open('tgux01sydx-9ztp.csv', encoding="utf-8") as framacalc_csv_file:
        reader = csv.DictReader(framacalc_csv_file)
        for row in reader:
            rgz_name = row['rgz']
            osm_name = row['name']
            ispravka = row['ispravka']
            if ispravka != '' and ispravka != '-':
                proper_name = ispravka
            else:
                proper_name = osm_name
            if proper_name != '':
                framacalc_csv.append({'rgz_name': rgz_name, 'name': proper_name})

    with open('curated_streets.csv', 'w', encoding="utf-8") as curated_streets_csv_file:
        writer = csv.DictWriter(
            curated_streets_csv_file,
            fieldnames=['rgz_name', 'name'])
        writer.writeheader()
        framacalc_csv = sorted(framacalc_csv, key=lambda x: x['rgz_name'])
        for entry in framacalc_csv:
            if entry['rgz_name'] == '':
                continue
                raise Exception()
            writer.writerow({
                'rgz_name': entry['rgz_name'],
                'name': entry['name']
            })


class StreetMapping:
    def __init__(self, cwd):
        self.street_mappings = {}
        with open(os.path.join(cwd, 'data', 'mapping', 'mapping.csv'), encoding='utf-8') as mapping_csv_file:
            reader = csv.DictReader(mapping_csv_file)
            for row in reader:
                self.street_mappings[row['rgz_name']] = [{'name': row['name'], 'source': row['source'], 'refs': row['refs'], 'opstina': ''}]
        with open(os.path.join(cwd, 'cureted_streets_per_opstina.csv'), encoding='utf-8') as mapping_csv_file:
            reader = csv.DictReader(mapping_csv_file)
            for row in reader:
                rgz_name = row['rgz_name']
                if rgz_name not in self.street_mappings:
                    raise Exception(f"Street {rgz_name} present in opstina overrides, but not in main mapping, quitting")
                self.street_mappings[rgz_name].append({'name': row['name'], 'source': 'curated', 'refs': '', 'opstina': row['opstina']})

    def get_all_rgz_names(self):
        """
        Gets a list with all RGZ names known
        """
        return self.street_mappings.keys()

    def get_all_names_for_rgz_name(self, rgz_name):
        """
        Gets array with all OSM names for a given RGZ name, with additional data (source, refs)
        """
        return self.street_mappings[rgz_name]


if __name__ == '__main__':
    main()
    #fix_framacalc()
