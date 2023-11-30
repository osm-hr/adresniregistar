# -*- coding: utf-8 -*-

import argparse
import ast
import os

import geopandas as gpd
import pandas as pd
from shapely import wkt

from common import normalize_name
from street_mapping import StreetMapping, best_effort_decapitalize


def collect_linestring(x):
    break_polygons = [(g if g.geom_type != 'Polygon' else g.boundary) for g in x]
    return gpd.tools.collect(break_polygons)


def do_analysis(opstina, data_path, street_mappings: StreetMapping):
    # This is how to get missing street name at new CSV
    # df_rgz = pd.read_csv(os.path.join(data_path, f'rgz/streets.csv'))
    # df_rgz['rgz_ulica_proper'] = df_rgz[['rgz_ulica', 'rgz_opstina']].apply(lambda x: street_mappings.get_name(x['rgz_ulica'], x['rgz_opstina'], default_value='foo'), axis=1)
    # df_missing_addresses = df_rgz[df_rgz.rgz_ulica_proper == 'foo']
    # df_missing_addresses['best_effort'] = df_missing_addresses['rgz_ulica'].apply(lambda x: best_effort_decapitalize(x))
    # pd.DataFrame(df_missing_addresses[['rgz_ulica', 'best_effort']]).to_csv(os.path.join(data_path, f'missing_streets.csv'), index=False)

    if os.path.exists(os.path.join(data_path, f'analysis/{opstina}.csv')):
        print(f"    Skipping {opstina}, already exists")
        return

    input_osm_file = os.path.join(data_path, f'osm/csv/{opstina}.csv')
    if not os.path.exists(input_osm_file):
        print(f"    Missing file {input_osm_file}, cannot process opstina {opstina}")
        return

    input_rgz_file = os.path.join(data_path, f'rgz/csv/{opstina}.csv')
    if not os.path.exists(input_rgz_file):
        print(f"    Missing file {input_rgz_file}, cannot process opstina {opstina}")
        return

    print(f"    Loading OSM streets in {opstina}")
    df_osm = pd.read_csv(input_osm_file, dtype={'ref:RS:ulica': object, 'osm_id': str})
    df_osm['osm_geometry2'] = df_osm.osm_geometry.apply(wkt.loads)
    df_osm['osm_id'] = df_osm['osm_id'].astype('str')
    gdf_osm = gpd.GeoDataFrame(df_osm, geometry='osm_geometry2', crs="EPSG:4326")
    gdf_osm.to_crs("EPSG:32634", inplace=True)
    gdf_osm['osm_geometry'] = gdf_osm.osm_geometry2
    gdf_osm['osm_name_norm'] = gdf_osm.osm_name.apply(normalize_name)
    gdf_osm['osm_way_length'] = gdf_osm.length
    gdf_osm.set_geometry('osm_geometry', inplace=True)
    gdf_osm['highway'] = df_osm['tags'].apply(lambda x: ast.literal_eval(x)['highway'])
    gdf_osm = gdf_osm[~gdf_osm.highway.isin(['footway', 'cycleway', 'path', 'steps', 'proposed', 'construction', 'corridor', 'platform'])]
    gdf_osm.drop(['osm_geometry2', 'highway'], inplace=True, axis=1)
    gdf_osm.sindex

    print(f"    Loading RGZ streets in {opstina}")
    df_rgz = pd.read_csv(input_rgz_file, dtype={'rgz_ulica_mb': str})
    df_rgz['rgz_geometry'] = df_rgz.rgz_geometry.apply(wkt.loads)
    gdf_rgz = gpd.GeoDataFrame(df_rgz, geometry='rgz_geometry', crs="EPSG:4326")
    gdf_rgz.to_crs("EPSG:32634", inplace=True)
    gdf_rgz['rgz_ulica_proper'] = gdf_rgz[['rgz_ulica', 'rgz_opstina']].apply(
        lambda x: street_mappings.get_name(x['rgz_ulica'], x['rgz_opstina'], default_value=''), axis=1)
    gdf_rgz['rgz_ulica_norm'] = gdf_rgz[['rgz_ulica', 'rgz_opstina']].apply(lambda x: normalize_name(
        street_mappings.get_name(x['rgz_ulica'], x['rgz_opstina'], default_value=x['rgz_ulica'])), axis=1)
    gdf_rgz['rgz_way_length'] = gdf_rgz.length
    gdf_rgz.sindex

    print(f"    Joining streets in RGZ and OSM in {opstina} by conflation (ref:RS:ulica)")
    gdf_rgz = gdf_rgz.merge(gdf_osm, how='left', left_on='rgz_ulica_mb', right_on='ref:RS:ulica')
    gdf_rgz.rename(columns={'osm_id': 'conflated_osm_id'}, inplace=True)
    gdf_rgz.drop(['osm_name', 'osm_name_sr', 'osm_name_sr_latn', 'osm_name_en',
                  'osm_alt_name', 'osm_alt_name_sr', 'osm_alt_name_sr_latn', 'osm_short_name', 'osm_short_name_sr',
                  'osm_short_name_sr_latn',
                  'osm_int_name', 'ref:RS:ulica', 'note', 'osm_name_norm'], inplace=True, axis=1)
    gdf_rgz.loc[pd.isna(gdf_rgz['conflated_osm_id']), 'conflated_osm_id'] = ''
    gdf_rgz['conflated_osm_id'] = gdf_rgz.groupby(['rgz_naselje_mb', 'rgz_ulica_mb'])['conflated_osm_id'].transform(
        lambda x: ','.join(x))
    gdf_rgz['conflated_osm_way_length'] = gdf_rgz.groupby(['rgz_naselje_mb', 'rgz_ulica_mb'])[
        'osm_way_length'].transform(lambda x: ','.join([str(round(i, 2)) for i in x]))
    gdf_rgz['osm_geometry'] = gdf_rgz[pd.notna(gdf_rgz.osm_geometry)].groupby(['rgz_naselje_mb', 'rgz_ulica_mb'])[
        'osm_geometry'].transform(lambda x: collect_linestring(x))
    gdf_rgz.osm_geometry.set_crs("EPSG:32634", inplace=True)
    gdf_rgz['conflated_max_error'] = gdf_rgz.rgz_geometry.hausdorff_distance(gdf_rgz.osm_geometry)
    gdf_rgz.drop_duplicates(subset=['rgz_naselje_mb', 'rgz_ulica_mb'], keep='first', inplace=True)
    gdf_rgz.drop(['osm_way_length'], inplace=True, axis=1)
    gdf_rgz.sindex

    print(f"    Buffering RGZ streets for 50m in {opstina}")
    gdf_rgz['rgz_buffered_geometry'] = gdf_rgz.rgz_geometry.buffer(distance=15)
    gdf_rgz.set_geometry('rgz_buffered_geometry', inplace=True)
    gdf_rgz.sindex

    # TODO: buffer naselja, ulice nekada mogu da budu malo preko
    # TODO: do quality checks for far away addresses
    # TODO: do quality checks for alt_name, short_name, int_name
    # TODO: detect round ways ("zaseoci")
    # TODO: refactor whole app
    # TODO: add overpass view on naselje
    """
    http://overpass-turbo.eu/?Q=node%5B%22amenity%22%3D%22drinking_water%22%5D(%7B%7Bbbox%7D%7D)%3B%0Aout%3B
[out:json][timeout:25];
area["name"="Србија"]["admin_level"=2]->.sr;
(
    area(area.sr)["boundary"="administrative"]["ref:RS:naselje"=801542]->.district;
    (
        way(area.district)["highway"]["highway"!="footway"]["highway"!="proposed"]["highway"!="cycleway"]["highway"!="construction"]["highway"!="steps"];
    );
);
(._;>;);
out;

{{style:
node {
  opacity: 0;
  symbol-size: 0;
  color: black;
}
way {
  color:red;
}
way[ref:RS:ulica] {
  color: black;
}
}}
    """
    gdf_osm['osm_geometry2'] = gdf_osm.osm_geometry

    print(f"    Joining streets in RGZ and OSM in {opstina} that have high IoU")
    gdf_osm_no_conflated = gdf_osm[gdf_osm["ref:RS:ulica"].isna()]
    gdf_high_intersection = gdf_rgz.sjoin(gdf_osm_no_conflated, how='inner', predicate='intersects')
    gdf_high_intersection['intersection_length'] = gdf_high_intersection['rgz_buffered_geometry'].intersection(
        gdf_high_intersection['osm_geometry2']).length
    gdf_high_intersection['found_intersection'] = gdf_high_intersection['intersection_length'] / gdf_high_intersection[
        'osm_geometry2'].length
    gdf_high_intersection.rename(columns={'osm_id': 'found_osm_id'}, inplace=True)
    gdf_high_intersection = gdf_high_intersection[gdf_high_intersection['found_intersection'] > 0.6]
    gdf_high_intersection.drop(['index_right', 'osm_name_sr', 'osm_name_sr_latn', 'osm_name_en',
                                'osm_alt_name', 'osm_alt_name_sr', 'osm_alt_name_sr_latn', 'osm_short_name',
                                'osm_short_name_sr', 'osm_short_name_sr_latn',
                                'osm_int_name', 'ref:RS:ulica', 'note', 'osm_geometry2', 'intersection_length'],
                               inplace=True, axis=1)

    # Bring back high IoU to RGZ. We can have here duplicated OSM streets that are in multiple RGZ streets.
    # We need to associate only one RGZ street per each OSM street, those with highest IoU.
    gdf_merge_with_iou = gdf_rgz.merge(gdf_high_intersection[
                                           ['rgz_naselje_mb', 'rgz_ulica_mb', 'osm_name', 'osm_name_norm',
                                            'found_intersection', 'found_osm_id', 'osm_way_length']], how='left',
                                       on=['rgz_naselje_mb', 'rgz_ulica_mb'])
    gdf_merge_with_iou['rank'] = 1
    gdf_merge_with_iou['rank'] = gdf_merge_with_iou.sort_values('found_intersection').groupby('found_osm_id')[
        'rank'].cumsum()
    gdf_merge_with_iou = gdf_merge_with_iou[gdf_merge_with_iou['rank'] == 1]

    # Bring back high IoU to RGZ. Now we have duplicated RGZ street that have multiple OSM candidates, collapse them
    gdf_rgz = gdf_rgz.merge(gdf_merge_with_iou[
                                ['rgz_naselje_mb', 'rgz_ulica_mb', 'osm_name', 'osm_name_norm', 'found_intersection',
                                 'found_osm_id', 'osm_way_length']], how='left', on=['rgz_naselje_mb', 'rgz_ulica_mb'])
    gdf_rgz['name_match'] = gdf_rgz[['rgz_ulica_proper', 'osm_name']].apply(
        lambda x: x['rgz_ulica_proper'] == x['osm_name'] and x['rgz_ulica_proper'] != '', axis=1)
    gdf_rgz['norm_name_match'] = gdf_rgz[['rgz_ulica_norm', 'osm_name']].apply(
        lambda x: x['rgz_ulica_norm'] == x['osm_name'] and x['rgz_ulica_norm'] != '', axis=1)
    gdf_rgz.loc[pd.isna(gdf_rgz['osm_name']), 'osm_name'] = ''
    gdf_rgz.loc[pd.isna(gdf_rgz['found_osm_id']), 'found_osm_id'] = ''
    import json
    gdf_rgz.loc[pd.isna(gdf_rgz['found_intersection']), 'found_intersection'] = ''
    gdf_rgz['found_osm_id'] = gdf_rgz.groupby(['rgz_naselje_mb', 'rgz_ulica_mb'])['found_osm_id'].transform(
        lambda x: ','.join(x))
    gdf_rgz['found_intersection'] = gdf_rgz.groupby(['rgz_naselje_mb', 'rgz_ulica_mb'])['found_intersection'].transform(
        lambda x: ','.join([str(x) for x in x]))
    gdf_rgz['found_osm_way_length'] = gdf_rgz.groupby(['rgz_naselje_mb', 'rgz_ulica_mb'])['osm_way_length'].transform(
        lambda x: ','.join([str(round(i, 2)) for i in x]))
    gdf_rgz['osm_name'] = gdf_rgz.groupby(['rgz_naselje_mb', 'rgz_ulica_mb'])['osm_name'].transform(
        lambda x: json.dumps(x.tolist(), ensure_ascii=False))
    gdf_rgz['name_match'] = gdf_rgz.groupby(['rgz_naselje_mb', 'rgz_ulica_mb'])['name_match'].transform(
        lambda x: ','.join(['1' if i else '0' for i in x]))
    gdf_rgz['norm_name_match'] = gdf_rgz.groupby(['rgz_naselje_mb', 'rgz_ulica_mb'])['norm_name_match'].transform(
        lambda x: ','.join(['1' if i else '0' for i in x]))
    gdf_rgz.drop_duplicates(subset=['rgz_naselje_mb', 'rgz_ulica_mb'], keep='first', inplace=True)
    gdf_rgz.drop(['osm_way_length'], inplace=True, axis=1)

    # At the end, save CSV
    gdf_rgz.drop(['rgz_buffered_geometry'], inplace=True, axis=1)
    print("    Saving analysis")
    gdf_rgz.set_geometry('osm_geometry', inplace=True)
    gdf_rgz.to_crs("EPSG:4326", inplace=True)
    gdf_rgz.set_geometry('rgz_geometry', inplace=True)
    gdf_rgz.to_crs("EPSG:4326", inplace=True)
    gdf_rgz.set_geometry('rgz_geometry', inplace=True)
    pd.DataFrame(gdf_rgz).to_csv(os.path.join(data_path, f'analysis/{opstina}.csv'), index=False)


def process_all_opstina(data_path, rgz_csv_path, street_mappings):
    total_csvs = len(os.listdir(rgz_csv_path))
    if total_csvs < 168:
        raise Exception("Some or all RGZ files missing! Bailing out")

    for i, file in enumerate(sorted(os.listdir(rgz_csv_path))):
        if not file.endswith(".csv"):
            continue
        opstina = file[:-4]
        print(f"{i + 1}/{total_csvs} Processing {opstina}")
        do_analysis(opstina, data_path, street_mappings)


def main():
    cwd = os.getcwd()
    data_path = os.path.join(cwd, 'data/')
    rgz_csv_path = os.path.join(data_path, 'rgz/csv')

    street_mappings = StreetMapping(os.path.join(cwd, '..', 'ar'))

    parser = argparse.ArgumentParser(
        description='create_st_analysis.py - Analyses opstine')
    parser.add_argument('--opstina', default=None, required=False, help='Opstina to process')
    args = parser.parse_args()
    if not args.opstina:
        process_all_opstina(data_path, rgz_csv_path, street_mappings)
    else:
        if not os.path.exists(os.path.join(rgz_csv_path, f'{args.opstina}.csv')):
            parser.error(f"File data/rgz/csv/{args.opstina}.csv do not exist")
            return
        do_analysis(args.opstina, data_path, street_mappings)


if __name__ == '__main__':
    main()
