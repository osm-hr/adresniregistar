# -*- coding: utf-8 -*-

import json
import os

import geopandas as gpd
import osmium
import pandas as pd
from shapely import wkt

from common import CollectRelationWaysHandler, CollectWayNodesHandler, BuildNodesCacheHandler, CollectEntitiesHandler, \
    AddressInBuildingResolution, cyr2lat


def is_simple_address(tags):
    common_tags = ['note', 'description', 'entrance', 'door', 'survey:date', 'survey_date', 'area',
                   'TEXT_ANGLE', 'TEXT_SIZE', 'OBJECTID', 'ref:RS:ulica', 'ref:RS:kucni_broj',
                   'building', 'building:levels', 'old_name', 'alt_name', 'source:addr', 'roof:levels',
                   'old_addr:street', 'old_addr:housenumber', 'access', 'removed:ref:RS:kucni_broj']
    for k in tags.keys():
        if not k.startswith("addr:") and k not in common_tags:
            return False
    return True


def is_poi(tags):
    poi_tags = ['shop', 'amenity', 'office', 'healthcare', 'tourism', 'leisure', 'craft', 'sport', 'power',
                'name', 'name:sr-Latn', 'wikidata', 'image', 'disused:shop', 'disused:amenity']
    for k in tags.keys():
        if k in poi_tags:
            return True
    return False


def result_or_note(has_note, potential_result):
    return potential_result if not has_note else AddressInBuildingResolution.NOTE_PRESENT


def do_resolution(input):
    # if building has address:
    #   if 1 POI and 0 addresses:
    #       if same address:
    #           POI to be moved to building
    #       else:
    #           weird situation, human to resolve
    #   if 1 address and 0 POI:
    #       if same address:
    #           we should remove address from building
    #       else:
    #           weird situation, human to resolve which address is correct (test if building has only partial address, like only street)
    #   if POI > 1 and 0 addresses:
    #       if all have same address between them and as building:
    #           all correct
    #       else:
    #           we should remove address from building
    #   if addresses > 1 and 0 POI:
    #       if all have same address between them and as building:
    #           delete all addresses, only building should remain
    #       else if all have same address between them and not as building:
    #           human should check
    #       else if they have different address between them:
    #           we should remove address from building
    #   if POI > 1 and addresses > 1:
    #       if all have same address between them and as building:
    #           delete all addresses, keep POI
    #       else if all have same address between them and not as building:
    #           human should check, human to resolve which address is correct
    #       else if they have different address between them:
    #           we should remove address from building

    # if building do not have address:
    #   if 1 POI and 0 addresses:
    #       POI to be moved to building
    #   if 1 address and 0 POI:
    #       we should remove address from building
    #   if POI > 1 and 0 addresses:
    #       if all have same address:
    #           put address on building too
    #       else:
    #           all correct
    #   if addresses > 1 and 0 POI:
    #       if all have same address between them:
    #           delete all addresses, only building should remain
    #       else:
    #           all correct
    #   if POI > 1 and addresses > 1:
    #       if all have same address between them:
    #           delete all addresses, put it on building, keep POI
    #       else:
    #           all correct
    if input['osm_id_right'].iloc[0][0] == 'n':
        # This is node, just bail out
        return AddressInBuildingResolution.BUILDING_IS_NODE

    has_note = input['tags_left'].apply(lambda x: 'note' in x).any() or\
               input['tags_right'].apply(lambda x: 'note' in x).any()

    building_has_address = input.building_has_address.iloc[0]
    poi_count = int(input.count_poi.iloc[0])
    address_count = int(input.count_addresses.iloc[0])

    if building_has_address:
        addresses_match = input.addresses_match.min()

        if poi_count == 1 and address_count == 0:
            if addresses_match:
                return AddressInBuildingResolution.NO_ACTION
            else:
                return result_or_note(has_note, AddressInBuildingResolution.ADDRESSES_NOT_MATCHING)
        if poi_count == 0 and address_count == 1:
            if addresses_match:
                return result_or_note(has_note, AddressInBuildingResolution.MERGE_ADDRESS_TO_BUILDING)
            else:
                osm_street_right = input['osm_street_right'].iloc[0]
                osm_housenumber_right = input['osm_housenumber_right'].iloc[0]
                osm_street_left = input['osm_street_left'].iloc[0]
                osm_housenumber_left = input['osm_housenumber_left'].iloc[0]
                if pd.notna(osm_street_right) and pd.notna(osm_street_left) and osm_street_left == osm_street_right:
                    if pd.isna(osm_housenumber_left) or pd.isna(osm_housenumber_right):
                        return result_or_note(has_note, AddressInBuildingResolution.MERGE_ADDRESS_TO_BUILDING)
                    else:
                        return result_or_note(has_note, AddressInBuildingResolution.ADDRESSES_NOT_MATCHING)
                elif pd.notna(osm_housenumber_left) and pd.notna(osm_housenumber_right) and osm_housenumber_left == osm_housenumber_right:
                    if pd.isna(osm_street_left) or pd.isna(osm_street_right):
                        return result_or_note(has_note, AddressInBuildingResolution.MERGE_ADDRESS_TO_BUILDING)
                    else:
                        return result_or_note(has_note, AddressInBuildingResolution.ADDRESSES_NOT_MATCHING)
        if poi_count > 1 and address_count == 0:
            different_address_count = len(input[['osm_street_left', 'osm_housenumber_left']].value_counts(dropna=False))
            if different_address_count == 1 and addresses_match:
                return AddressInBuildingResolution.NO_ACTION
            if different_address_count == 1 and not addresses_match:
                return result_or_note(has_note, AddressInBuildingResolution.ADDRESSES_NOT_MATCHING)
            if different_address_count > 1:
                return result_or_note(has_note, AddressInBuildingResolution.REMOVE_ADDRESS_FROM_BUILDING)
            raise Exception("cannot reach here")
        if poi_count == 0 and address_count > 1:
            different_address_count = len(input[['osm_street_left', 'osm_housenumber_left']].value_counts(dropna=False))
            if different_address_count == 1 and addresses_match:
                return result_or_note(has_note, AddressInBuildingResolution.MERGE_ADDRESS_TO_BUILDING)
            if different_address_count == 1 and not addresses_match:
                return result_or_note(has_note, AddressInBuildingResolution.ADDRESSES_NOT_MATCHING)
            if different_address_count > 1:
                return result_or_note(has_note, AddressInBuildingResolution.REMOVE_ADDRESS_FROM_BUILDING)
            raise Exception("cannot reach here")
        if poi_count >= 1 and address_count >= 1:
            return result_or_note(has_note, AddressInBuildingResolution.CASE_TOO_COMPLEX)

    # case where building don't have address
    if poi_count == 1 and address_count == 0:
        return result_or_note(has_note, AddressInBuildingResolution.MERGE_POI_TO_BUILDING)
    if poi_count == 0 and address_count == 1:
        return result_or_note(has_note, AddressInBuildingResolution.MERGE_ADDRESS_TO_BUILDING)
    if poi_count > 1 and address_count == 0:
        different_address_count = len(input[['osm_street_left', 'osm_housenumber_left']].value_counts(dropna=False))
        if different_address_count == 1:
            return result_or_note(has_note, AddressInBuildingResolution.COPY_POI_ADDRESS_TO_BUILDING)
        else:
            return AddressInBuildingResolution.NO_ACTION
    if poi_count == 0 and address_count > 1:
        different_address_count = len(input[['osm_street_left', 'osm_housenumber_left']].value_counts(dropna=False))
        if different_address_count == 1:
            return result_or_note(has_note, AddressInBuildingResolution.MERGE_ADDRESS_TO_BUILDING)
        else:
            return result_or_note(has_note, AddressInBuildingResolution.ATTACH_ADDRESSES_TO_BUILDING)
    if poi_count >= 1 and address_count >= 1:
        return result_or_note(has_note, AddressInBuildingResolution.CASE_TOO_COMPLEX)
    raise Exception("cannot reach here")


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


def find_unaccounted_osm_addresses(cwd):
    osm_path = os.path.join(cwd, 'data/osm')
    rgz_path = os.path.join(cwd, 'data/rgz')
    qa_path = os.path.join(cwd, 'data/qa')
    pbf_file = os.path.join(osm_path, 'download/serbia.osm.pbf')

    if os.path.exists(os.path.join(qa_path, 'unaccounted_osm_addresses.csv')):
        return

    # Build building geometries
    crwh = CollectRelationWaysHandler('addr:housenumber')
    crwh.apply_file(pbf_file)
    print(f"Collected all ways ({len(crwh.ways)}) from building relations")

    cwnh = CollectWayNodesHandler(crwh.ways, 'addr:housenumber')
    cwnh.apply_file(pbf_file)
    print(f"Collected all nodes ({len(cwnh.nodes)}) from building ways")

    bnch = BuildNodesCacheHandler(set(cwnh.nodes))
    bnch.apply_file(pbf_file)
    print(f"Found coordinates for all nodes ({len(bnch.nodes_cache)}) for all addr:housenumber")

    ceh = CollectEntitiesHandler(bnch.nodes_cache, cwnh.ways_cache, 'addr:housenumber', collect_tags=True)
    ceh.apply_file(pbf_file)
    gdf_osm_addresses = gpd.GeoDataFrame(ceh.entities, geometry='osm_geometry', crs="EPSG:4326")
    gdf_osm_addresses = gdf_osm_addresses[pd.isna(gdf_osm_addresses['ref:RS:kucni_broj'])]
    gdf_osm_addresses.sindex
    print(f"Found all building geometries ({len(ceh.entities)}) from PBF")

    # Remove those with "removed:ref:RS:kucni_broj" tag, as they are counted differently (as removed)
    gdf_osm_addresses['is_removed'] = gdf_osm_addresses['tags'].apply(lambda tags: True if 'removed:ref:RS:kucni_broj' in tags else False)
    gdf_osm_addresses = gdf_osm_addresses[~gdf_osm_addresses.is_removed]

    # For testing purposes, save and load gdf_buildings like this
    # pd.DataFrame(gdf_osm_addresses).to_csv('~/src/adresniregistar/ar/data/gdf_osm_addresses.csv', index=False)
    # gdf_osm_addresses = pd.read_csv('~/src/adresniregistar/ar/data/gdf_osm_addresses.csv')
    # gdf_osm_addresses['osm_geometry'] = gdf_osm_addresses.osm_geometry.apply(wkt.loads)
    # gdf_osm_addresses = gpd.GeoDataFrame(gdf_osm_addresses, geometry='osm_geometry', crs="EPSG:4326")
    # gdf_osm_addresses.sindex

    df_opstine = pd.read_csv(os.path.join(rgz_path, 'opstina.csv'))
    df_opstine['geometry'] = df_opstine.wkt.apply(wkt.loads)
    gdf_opstine = gpd.GeoDataFrame(df_opstine, geometry='geometry', crs="EPSG:32634")
    gdf_opstine.to_crs("EPSG:4326", inplace=True)
    gdf_opstine.sindex
    print(f"Loaded all opstine geometries ({len(gdf_opstine)})")

    addresses_per_opstina = gdf_osm_addresses.sjoin(gdf_opstine, how='inner', predicate='intersects')
    addresses_per_opstina.sindex
    addresses_per_opstina['name'] = addresses_per_opstina['tags'].apply(lambda x: x['name'] if 'name' in x else '')
    addresses_per_opstina['amenity'] = addresses_per_opstina['tags'].apply(lambda x: x['amenity'] if 'amenity' in x else '')
    addresses_per_opstina['shop'] = addresses_per_opstina['tags'].apply(lambda x: x['shop'] if 'shop' in x else '')

    addresses_per_opstina.drop(['osm_country', 'osm_city', 'osm_postcode', 'ref:RS:kucni_broj', 'tags', 'index_right',
                                'opstina_maticni_broj', 'opstina_ime', 'opstina_povrsina', 'okrug_sifra', 'okrug_ime',
                                'okrug_imel', 'wkt', 'is_removed'],
                               inplace=True, axis=1)
    print("Split all addresses per opstina")

    pd.DataFrame(addresses_per_opstina).to_csv(os.path.join(qa_path, 'unaccounted_osm_addresses.csv'), index=False)
    print("Created unaccounted_osm_addresses.csv")


def find_addresses_in_buildings(cwd):
    osm_path = os.path.join(cwd, 'data/osm')
    rgz_path = os.path.join(cwd, 'data/rgz')
    qa_path = os.path.join(cwd, 'data/qa')
    pbf_file = os.path.join(osm_path, 'download/serbia.osm.pbf')

    if os.path.exists(os.path.join(qa_path, 'addresses_in_buildings_per_opstina.csv')):
        return

    # Build building geometries
    crwh = CollectRelationWaysHandler('building')
    crwh.apply_file(pbf_file)
    print(f"Collected all ways ({len(crwh.ways)}) from building relations")

    cwnh = CollectWayNodesHandler(crwh.ways, 'building')
    cwnh.apply_file(pbf_file)
    print(f"Collected all nodes ({len(cwnh.nodes)}) from building ways")

    bnch = BuildNodesCacheHandler(set(cwnh.nodes))
    bnch.apply_file(pbf_file)
    print(f"Found coordinates for all nodes ({len(bnch.nodes_cache)}) for all buildings")

    ceh = CollectEntitiesHandler(bnch.nodes_cache, cwnh.ways_cache, 'building', collect_tags=True)
    ceh.apply_file(pbf_file)
    gdf_buildings = gpd.GeoDataFrame(ceh.entities, geometry='osm_geometry', crs="EPSG:4326")
    gdf_buildings.sindex
    print(f"Found all building geometries ({len(ceh.entities)}) from PBF")

    # For testing purposes, save and load gdf_buildings like this
    # pd.DataFrame(gdf_buildings).to_csv('~/src/adresniregistar/ar/data/gdf_buildings.csv', index=False)
    # gdf_buildings = pd.read_csv('~/src/adresniregistar/ar/data/gdf_buildings.csv')
    # gdf_buildings['osm_geometry'] = gdf_buildings.osm_geometry.apply(wkt.loads)
    # gdf_buildings = gpd.GeoDataFrame(gdf_buildings, geometry='osm_geometry', crs="EPSG:4326")
    # gdf_buildings.sindex

    # # Build node geometries
    ceh = CollectEntitiesHandler(nodes_cache=set(), ways_cache=set(), tag_to_search='addr:housenumber',
                                 collect_only_nodes=True, collect_tags=True)
    ceh.apply_file(pbf_file)
    gdf_addresses = gpd.GeoDataFrame(ceh.entities, geometry='osm_geometry', crs="EPSG:4326")
    gdf_addresses.sindex
    print(f"Found all address nodes ({len(ceh.entities)}) from PBF")

    df_opstine = pd.read_csv(os.path.join(rgz_path, 'opstina.csv'))
    df_opstine['geometry'] = df_opstine.wkt.apply(wkt.loads)
    gdf_opstine = gpd.GeoDataFrame(df_opstine, geometry='geometry', crs="EPSG:32634")
    gdf_opstine.to_crs("EPSG:4326", inplace=True)
    gdf_opstine.sindex
    print(f"Loaded all opstine geometries ({len(gdf_opstine)})")

    addresses_per_opstina = gdf_addresses.sjoin(gdf_opstine, how='inner', predicate='intersects')
    addresses_per_opstina.sindex
    addresses_per_opstina.drop(['osm_country', 'osm_city', 'osm_postcode', 'index_right', 'opstina_maticni_broj',
                                'opstina_ime', 'opstina_povrsina', 'okrug_sifra', 'okrug_ime', 'okrug_imel', 'wkt'],
                               inplace=True, axis=1)
    print("Split all addresses per opstina")

    # For testing purposes, save and load addresses_per_opstina like this
    # pd.DataFrame(addresses_per_opstina).to_csv('~/src/adresniregistar/ar/data/addresses_per_opstina.csv', index=False)
    # addresses_per_opstina = pd.read_csv('~/src/adresniregistar/ar/data/addresses_per_opstina.csv')
    # addresses_per_opstina['osm_geometry'] = addresses_per_opstina.osm_geometry.apply(wkt.loads)
    # addresses_per_opstina = gpd.GeoDataFrame(addresses_per_opstina, geometry='osm_geometry', crs="EPSG:4326")
    # addresses_per_opstina.sindex

    addresses_in_buildings_per_opstina = addresses_per_opstina.sjoin(gdf_buildings, how='inner', predicate='within')
    addresses_in_buildings_per_opstina.drop(['osm_country', 'osm_city', 'osm_postcode'], inplace=True, axis=1)

    # Calculate resolution (what to report, what not, what should be merged, what should be removed...)
    df = addresses_in_buildings_per_opstina
    df['building_has_address'] = df.apply(
        lambda row: pd.notna(row.osm_street_right) or pd.notna(row.osm_housenumber_right), axis=1)
    df['addresses_match'] = df.apply(lambda row:
                                     row.osm_street_left == row.osm_street_right and
                                     row.osm_housenumber_left == row.osm_housenumber_right, axis=1)
    # df['tags_left'] = df.apply(lambda row: ast.literal_eval(row.tags_left), axis=1)
    df['node_is_simple_address'] = df.apply(lambda row: is_simple_address(row.tags_left), axis=1)
    df['node_is_poi'] = df.apply(lambda row: is_poi(row.tags_left), axis=1)

    both_false = df[(df.node_is_simple_address == False) & (df.node_is_poi == False)]
    both_true = df[(df.node_is_simple_address == True) & (df.node_is_poi == True)]
    if len(both_false) > 0:
        print(f"There are {len(both_false)} entities which are neither simple address nor POI, take a look")
    if len(both_true) > 0:
        print(f"There are {len(both_true)} entities which are both simple addresses and POIs, take a look")

    # Very convoluted way to count POIs for each group
    count_poi_df = df[df.node_is_poi == True].groupby(['osm_id_right'])['osm_id_right'].transform('count')
    count_poi_df = count_poi_df.to_frame()
    count_poi_df.rename(columns={'osm_id_right': 'count_poi'}, inplace=True)
    df = df.join(count_poi_df)
    df.fillna(value={'count_poi': 0}, inplace=True)
    df['count_poi'] = df.groupby(['osm_id_right'])['count_poi'].transform('max')

    # Very convoluted way to count addresses for each group
    count_addresses_df = df[df.node_is_simple_address==True].groupby(['osm_id_right'])['osm_id_right'].transform('count')
    count_addresses_df = count_addresses_df.to_frame()
    count_addresses_df.rename(columns={'osm_id_right': 'count_addresses'}, inplace=True)
    df = df.join(count_addresses_df)
    df.fillna(value={'count_addresses': 0}, inplace=True)
    df['count_addresses'] = df.groupby(['osm_id_right'])['count_addresses'].transform('max')

    df['addresses_match'] = df.apply(
        lambda row:
        ((row.osm_street_left == row.osm_street_right) or (pd.isna(row.osm_street_left) and pd.isna(row.osm_street_right)))
        and
        ((row.osm_housenumber_left == row.osm_housenumber_right) or (pd.isna(row.osm_housenumber_left) and pd.isna(row.osm_housenumber_right))),
        axis=1)

    resolutions = df.groupby(['osm_id_right']).apply(do_resolution)
    df = df.join(resolutions.rename('resolution'), on='osm_id_right')
    df['resolution'] = df['resolution'].apply(lambda x: x.value)
    df = df[df.resolution != AddressInBuildingResolution.NO_ACTION.value]

    pd.DataFrame(df).to_csv(os.path.join(qa_path, 'addresses_in_buildings_per_opstina.csv'), index=False)
    print("Created addresses_in_buildings_per_opstina.csv")


def find_duplicated_refs(cwd):
    # Finds addresses which have same ref:RS:kucni_broj reference
    osm_path = os.path.join(cwd, 'data/osm')
    rgz_path = os.path.join(cwd, 'data/rgz')
    pbf_file = os.path.join(osm_path, 'download/serbia.osm.pbf')
    qa_path = os.path.join(cwd, 'data/qa')
    json_file_path = os.path.join(qa_path, 'duplicated_refs.json')

    crah = CollectRefAddressesHandler()
    crah.apply_file(pbf_file)
    print(f"Found all addresses with refs ({len(crah.addresses)} from PBF")

    if os.path.exists(json_file_path):
        print("File data/qa/duplicated_refs.json already exists")
        return

    output_dict = []
    for k, v in crah.addresses.items():
        streets_set = set([s['tags']['addr:street'] if 'addr:street' in s['tags'] else '' for s in v])
        housenumbers_set = set([s['tags']['addr:housenumber'] if 'addr:housenumber' in s['tags'] else '' for s in v])
        streets_same = len(streets_set) == 1 or '' in streets_set
        housenumbers_same = len(housenumbers_set) == 1 or '' in housenumbers_set
        different_addresses = not streets_same or not housenumbers_same
        if different_addresses:
            output_dict.append({
                'ref:RS:kucni_broj': k,
                'duplicates': v
            })

    input_rgz_file = os.path.join(rgz_path, 'addresses.csv')
    if not os.path.exists(input_rgz_file):
        print(f"    Missing file {input_rgz_file}, cannot load RGZ addresses")
        return
    df_rgz = pd.read_csv(input_rgz_file, dtype={'rgz_kucni_broj_id': str})
    for dup in output_dict:
        ref = dup['ref:RS:kucni_broj']
        founed_entries = df_rgz[df_rgz.rgz_kucni_broj_id == ref]
        if len(founed_entries) > 0:
            dup['opstina_imel'] = cyr2lat(founed_entries.iloc[0]['rgz_opstina'])
        else:
            dup['opstina_imel'] = 'N/A'

    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(output_dict, json_file, ensure_ascii=False)


def main():
    cwd = os.getcwd()
    find_addresses_in_buildings(cwd)
    find_duplicated_refs(cwd)
    find_unaccounted_osm_addresses(cwd)


if __name__ == '__main__':
    main()
