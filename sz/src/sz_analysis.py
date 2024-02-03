# -*- coding: utf-8 -*-

import argparse
import json
import os.path
import ast

import numpy as np
import osmium
import pandas as pd

from common import cyr2lat, ApartmentResolution, normalize_name


# TODO: add support for street mapping to multiple street names
# TODO: case where there is building:part which is part of relation (https://www.openstreetmap.org/way/809281977)
# TODO: add support where node is attached to way which is attached to relation


class CollectApartmentsHandler(osmium.SimpleHandler):
    def __init__(self, entites):
        osmium.SimpleHandler.__init__(self)
        self.relation_to_search = set([int(e[1:]) for e in entites if e[0] == 'r'])
        self.ways_to_search = set([int(e[1:]) for e in entites if e[0] == 'w'])
        self.nodes_to_search = set([int(e[1:]) for e in entites if e[0] == 'n'])
        self.relations = {}
        self.ways = {}
        self.node2way_mapping = {}

    def relation(self, r):
        if r.id in self.relation_to_search:
            self.relations[r.id] = {k: v for k, v in r.tags}

    def way(self, w):
        if w.id in self.ways_to_search:
            self.ways[w.id] = {k: v for k, v in w.tags}
        for n in w.nodes:
            if n.ref in self.nodes_to_search:
                if n.ref not in self.node2way_mapping:
                    self.node2way_mapping[n.ref] = []
                self.node2way_mapping[n.ref].append({
                    "way_id": w.id,
                    "tags": {k: v for k, v in w.tags}
                })


def normalize_street(street):
    return street.replace(' ', '').replace('.', '')


def get_resolution_single_entity(cah: CollectApartmentsHandler, df_addresses_in_buildings, osm_id) -> ApartmentResolution:
    if pd.isna(osm_id):
        return np.nan

    id_int = int(osm_id[1:])
    if osm_id[0] == 'n':
        if id_int in cah.node2way_mapping:
            way_listing = cah.node2way_mapping[id_int]
            any_apartment = len([w for w in way_listing if 'building' in w['tags'] and w['tags']['building'] == 'apartments']) > 0
            any_building = len([w for w in way_listing if 'building' in w['tags']]) > 0
            if any_apartment:
                return ApartmentResolution.OSM_ENTITY_APARTMENT
            if any_building:
                return ApartmentResolution.OSM_ENTITY_NOT_APARTMENT
            return ApartmentResolution.OSM_ENTITY_NOT_BUILDING
        else:
            nodes_inside_building = df_addresses_in_buildings[df_addresses_in_buildings['osm_id_left'] == osm_id]
            if len(nodes_inside_building) == 0:
                return ApartmentResolution.NODE_DETACHED
            else:
                tags = ast.literal_eval(list(nodes_inside_building['tags_right'])[0])
                if 'building' not in tags:
                    return ApartmentResolution.OSM_ENTITY_NOT_BUILDING
                elif tags['building'] != 'apartments':
                    return ApartmentResolution.OSM_ENTITY_NOT_APARTMENT
                else:
                    return ApartmentResolution.OSM_ENTITY_APARTMENT
    if osm_id[0] == 'w':
        if id_int in cah.ways:
            way = cah.ways[id_int]
            if 'building' in way:
                if way['building'] != 'apartments':
                    return ApartmentResolution.OSM_ENTITY_NOT_APARTMENT
                else:
                    return ApartmentResolution.OSM_ENTITY_APARTMENT
            else:
                return ApartmentResolution.OSM_ENTITY_NOT_BUILDING
        else:
            return ApartmentResolution.OSM_ENTITY_NOT_FOUND
    if osm_id[0] == 'r':
        if id_int in cah.relations:
            relation = cah.relations[id_int]
            if 'building' in relation:
                if relation['building'] != 'apartments':
                    return ApartmentResolution.OSM_ENTITY_NOT_APARTMENT
                else:
                    return ApartmentResolution.OSM_ENTITY_APARTMENT
            else:
                return ApartmentResolution.OSM_ENTITY_NOT_BUILDING
        else:
            return ApartmentResolution.OSM_ENTITY_NOT_FOUND
    raise Exception(f'Unknown osm id type {osm_id}')


def get_resolution(cah: CollectApartmentsHandler, df_addresses_in_buildings, osm_ids):
    if pd.isna(osm_ids):
        return np.nan

    osm_id_list = json.loads(osm_ids)
    if len(osm_id_list) == 0:
        return np.nan

    max_resolution = None
    for osm_id in osm_id_list:
        resolution = get_resolution_single_entity(cah, df_addresses_in_buildings, osm_id)
        if not max_resolution or resolution.value > max_resolution.value:
            max_resolution = resolution
    return max_resolution


def join_dz_rgz_osm(ar_data_path: str, df_sz, opstina):
    opstina_latin = cyr2lat(opstina)
    # Take OSM data with ref:RS:kucni_broj
    df_osm = pd.read_csv(os.path.join(ar_data_path, f'osm/csv/{opstina_latin}.csv'), dtype={'ref:RS:ulica': object, 'ref:RS:kucni_broj': object})
    df_osm = df_osm[pd.notna(df_osm['ref:RS:kucni_broj'])]
    df_osm['ref:RS:kucni_broj'] = df_osm['ref:RS:kucni_broj'].astype('string')

    # Take RGZ data and normalize for join
    df_rgz = pd.read_csv(os.path.join(ar_data_path, f'rgz/csv/{normalize_name(opstina_latin.lower())}.csv'), dtype={'rgz_kucni_broj_id': str})
    df_rgz['rgz_ulica_norm'] = df_rgz.rgz_ulica.apply(lambda x: normalize_street(x))
    df_rgz['rgz_kucni_broj_id'] = df_rgz['rgz_kucni_broj_id'].astype('string')

    # Join stambene zajednice and RGZ by opstina, normalized street and housenumber
    df_sz_rgz = df_sz.merge(df_rgz, how='left',
                         left_on=['sz_opstina', 'sz_ulica_norm', 'sz_kucni_broj'],
                         right_on=['rgz_opstina', 'rgz_ulica_norm', 'rgz_kucni_broj'])
    df_sz_rgz['found_in_rgz'] = pd.notna(df_sz_rgz.rgz_kucni_broj)
    df_sz_rgz.drop(['rgz_opstina_mb', 'rgz_opstina', 'rgz_naselje_mb', 'rgz_ulica_mb'], inplace=True, axis=1)

    # remove duplicates (but remember what are naselja with same street/housenumber)
    df_sz_rgz['rgz_naselje'] = df_sz_rgz['rgz_naselje'].astype('string')
    df_sz_rgz['rgz_naselje'] = df_sz_rgz['rgz_naselje'].fillna('')
    df_sz_rgz['is_duplicated'] = df_sz_rgz.duplicated(subset=['sz_opstina', 'sz_ulica', 'sz_kucni_broj'], keep=False)

    df_sz_rgz['duplicated_naselja'] = df_sz_rgz.groupby(['sz_opstina', 'sz_ulica', 'sz_kucni_broj'])['rgz_naselje'].transform(lambda x: ','.join(x))
    df_sz_rgz.drop_duplicates(subset=['sz_opstina', 'sz_ulica', 'sz_kucni_broj'], keep='first', inplace=True)
    df_sz_rgz['found_in_rgz'] = df_sz_rgz.apply(lambda row: row['found_in_rgz'] and not row['is_duplicated'], axis=1)
    df_sz_rgz['rgz_kucni_broj_id'] = df_sz_rgz.apply(lambda row: row['rgz_kucni_broj_id'] if row['found_in_rgz'] else np.nan, axis=1)

    # join with OSM
    df_sz_rgz_osm = df_sz_rgz.merge(df_osm, how='left', left_on='rgz_kucni_broj_id', right_on='ref:RS:kucni_broj')
    df_sz_rgz_osm.drop(['osm_country', 'osm_city', 'osm_postcode', 'ref:RS:ulica', 'osm_geometry', 'tags'], inplace=True, axis=1)
    df_sz_rgz_osm['found_in_osm'] = pd.notna(df_sz_rgz_osm['osm_id'])

    # remove duplicated (it is complicated as we need to remove duplicated "rgz_kucni_broj_id", but they can be NaN too
    df_sz_rgz_osm['is_osm_duplicated'] = df_sz_rgz_osm.duplicated(subset=['rgz_kucni_broj_id'], keep=False)
    df_sz_rgz_osm['is_osm_duplicated'] = df_sz_rgz_osm.apply(lambda row: row['is_osm_duplicated'] and pd.notna(row['rgz_kucni_broj_id']), axis=1)

    df_sz_rgz_osm['osm_id'] = df_sz_rgz_osm.groupby(['rgz_kucni_broj_id'])['osm_id'].transform(lambda x: json.dumps(list(x)))
    df_sz_rgz_osm['osm_id'] = df_sz_rgz_osm.apply(lambda row: row['osm_id'] if row['found_in_osm'] else np.nan, axis=1)
    df_sz_rgz_osm['osm_street'] = df_sz_rgz_osm.groupby(['rgz_kucni_broj_id'])['osm_street'].transform(lambda x: json.dumps(list(x), ensure_ascii=False))
    df_sz_rgz_osm['osm_street'] = df_sz_rgz_osm.apply(lambda row: row['osm_street'] if row['found_in_osm'] else np.nan, axis=1)
    df_sz_rgz_osm['osm_housenumber'] = df_sz_rgz_osm.groupby(['rgz_kucni_broj_id'])['osm_housenumber'].transform(lambda x: json.dumps(list(x), ensure_ascii=False))
    df_sz_rgz_osm['osm_housenumber'] = df_sz_rgz_osm.apply(lambda row: row['osm_housenumber'] if row['found_in_osm'] else np.nan, axis=1)

    df_sz_rgz_osm['is_osm_duplicated_temp'] = df_sz_rgz_osm.duplicated(subset=['rgz_kucni_broj_id'], keep='first')
    df_sz_rgz_osm.drop(df_sz_rgz_osm[(df_sz_rgz_osm.is_osm_duplicated) & (df_sz_rgz_osm.is_osm_duplicated_temp)].index, inplace=True)
    df_sz_rgz_osm.drop(['is_osm_duplicated', 'is_osm_duplicated_temp'], inplace=True, axis=1)

    return df_sz_rgz_osm


def main(ar_data_path: str):
    cwd = os.getcwd()
    data_path = os.path.join(cwd, 'data/')
    registar_sz_csv_path = os.path.join(data_path, 'registarstambenihzajednica.csv')
    analysis_csv_path = os.path.join(data_path, 'sz_analysis.csv')

    if os.path.exists(analysis_csv_path):
        print('File data/sz_analysis.csv already exist')
        return

    # Take stambene zajednice and normalize for join
    df_sz = pd.read_csv(registar_sz_csv_path)
    df_sz.rename(columns={
            'OkrugNaziv1': 'sz_okrug',
            'OpstinaNaziv1': 'sz_opstina',
            'PoslovnoIme': 'sz_ime',
            'Ulica': 'sz_ulica',
            'KucniBroj': 'sz_kucni_broj'
        }, inplace=True)
    df_sz['sz_ulica_norm'] = df_sz.sz_ulica.apply(lambda x: normalize_street(x))
    df_sz['sz_kucni_broj'] = df_sz['sz_kucni_broj'].astype('string')
    # sometimes there are duplicates in original dataset, remove them
    df_sz.drop_duplicates(subset=['sz_opstina', 'sz_ulica', 'sz_kucni_broj'], keep='first', inplace=True)

    # Join with RGZ and OSM data per opstina
    df_sz_rgz_osms = []
    for i, opstina in enumerate(list(df_sz.sz_opstina.unique())):
        print(f'{i+1}/{len(df_sz.sz_opstina.unique())} Processing {opstina}')
        df_sz_rgz_osms.append(join_dz_rgz_osm(ar_data_path, df_sz[df_sz.sz_opstina == opstina], opstina))
    df_sz_rgz_osm = pd.concat(df_sz_rgz_osms)

    # extract tags from OSM
    osm_ids = list(df_sz_rgz_osm[pd.notna(df_sz_rgz_osm['osm_id'])].apply(lambda row: json.loads(row['osm_id']), axis=1).explode())
    cah = CollectApartmentsHandler(osm_ids)
    cah.apply_file(os.path.join(ar_data_path, 'osm/download/serbia.osm.pbf'))

    # Example to persist OSM data for faster debugging
    # if os.path.exists('cah.pickle'):
    #     cah = CollectApartmentsHandler(osm_ids)
    #     with open('cah.pickle', 'rb') as f:
    #         d = pickle.load(f)
    #     cah.relations = d['relations']
    #     cah.ways = d['ways']
    #     cah.node2way_mapping = d['node2way_mapping']
    # else:
    #     cah = CollectApartmentsHandler(osm_ids)
    #     cah.apply_file(os.path.join(ar_data_path, 'osm/download/serbia.osm.pbf'))
    #     with open('cah.pickle', 'wb') as f:
    #         pickle.dump({"relations": cah.relations, "ways": cah.ways, "node2way_mapping": cah.node2way_mapping}, f)

    # Calculate resolution
    df_addresses_in_buildings = pd.read_csv(os.path.join(os.path.join(ar_data_path, 'qa/addresses_in_buildings_per_opstina.csv')))

    df_sz_rgz_osm['resolution'] = df_sz_rgz_osm.osm_id.apply(lambda osm_id: get_resolution(cah, df_addresses_in_buildings, osm_id))
    df_sz_rgz_osm['resolution'] = df_sz_rgz_osm.resolution.apply(lambda x: x.value if pd.notna(x) else np.nan)

    # dump to report
    df_sz_rgz_osm.to_csv(analysis_csv_path, index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='sz_analysis.py - analiza stambenih zajednica')
    parser.add_argument('--data-path', default=None, required=True, help='Path to data where .pbf, processed opstine and addresses in buildings reside')
    args = parser.parse_args()
    if not os.path.exists(args.data_path) or not os.path.isdir(args.data_path):
        parser.exit(f'Data path {args.data_path} does not exist or is not directory')
        exit()
    main(args.data_path)
