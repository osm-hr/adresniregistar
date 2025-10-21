import argparse
import json
import os

import pandas as pd

from common import normalize_name
from street_mapping import StreetMapping


def calculate_name_match(street):
    total_length = 0
    average_length = 0
    total_count_wrong = 0

    found_osm_ids = street['found_osm_id'].split(',')
    name_matches = [True if x == '1' else False for x in street['name_match'].split(',')]
    norm_name_matches = [True if x == '1' else False for x in street['norm_name_match'].split(',')]
    osm_names = json.loads(street['osm_name'])
    found_intersections = str(street['found_intersection']).split(',')
    found_osm_way_lengths = str(street['found_osm_way_length']).split(',')
    assert len(found_osm_ids) == len(found_intersections)
    assert len(found_osm_ids) == len(found_osm_way_lengths)
    assert len(found_osm_ids) == len(name_matches)
    assert len(found_osm_ids) == len(norm_name_matches)
    assert len(found_osm_ids) == len(osm_names)

    for found_intersection, found_osm_way_length, osm_name, name_match, norm_name_match in zip(found_intersections, found_osm_way_lengths, osm_names, name_matches, norm_name_matches):
        wrong_name = osm_name != '' and not name_match and not norm_name_match
        if wrong_name:
            total_length = total_length + float(found_osm_way_length)
            average_length = average_length + float(found_intersection) * float(found_osm_way_length)
            total_count_wrong += 1
    return total_length, average_length, int(total_count_wrong)


def calculate_geom_missing(street):
    """
    Returns tuple of 2 length defining whether:
    * length of missing geometry that needs to be drawn in OSM
    * length of missing geometry that is in OSM and just needs conflation
    """

    rgz_length = street['rgz_way_length']
    rgz_covered = street['rgz_way_length_covered']
    conflated_max_error = street['conflated_max_error']
    rgz_missing = min(rgz_length - rgz_covered, conflated_max_error)

    conflated_lengths = []
    max_conflated_length = 0
    if pd.notna(street['found_osm_id']):
        found_osm_ids = street['found_osm_id'].split(',')
        name_matches = [True if x == '1' else False for x in street['name_match'].split(',')]
        norm_name_matches = [True if x == '1' else False for x in street['norm_name_match'].split(',')]
        osm_names = json.loads(street['osm_name'])
        found_intersections = str(street['found_intersection']).split(',')
        found_osm_way_lengths = str(street['found_osm_way_length']).split(',')
        assert len(found_osm_ids) == len(found_intersections)
        assert len(found_osm_ids) == len(found_osm_way_lengths)
        assert len(found_osm_ids) == len(name_matches)
        assert len(found_osm_ids) == len(norm_name_matches)
        assert len(found_osm_ids) == len(osm_names)
        for found_intersection, found_osm_way_length in zip(found_intersections, found_osm_way_lengths):
            length = float(found_intersection) * float(found_osm_way_length)
            conflated_lengths.append(length)
            if length > max_conflated_length:
                max_conflated_length = length
    conflated_lengths_sum = sum(conflated_lengths)

    if rgz_missing <= 50:
        # Total missing length is less than 50m, nothing here
        return 0, 0

    if max_conflated_length <= 50:
        # There are no conflation candidates. It seems it needs drawing
        return rgz_missing, 0
    else:
        return 0, conflated_lengths_sum
    #print(f"{street['rgz_ulica_mb']},{rgz_length},{rgz_covered},{conflated_max_error},{max_conflated_length}")


def do_analysis_name_mismatch(opstina, data_path, require_return):
    output_path = os.path.join(data_path, f'qa/name_mismatch/{opstina}.csv')
    if not require_return and os.path.exists(output_path):
        print(f"    Skipping {opstina}, already exists")
        return

    input_analysis_file = os.path.join(data_path, f'analysis/{opstina}.csv')
    if not require_return and not os.path.exists(input_analysis_file):
        print(f"    Missing file {input_analysis_file}, cannot process opstina {opstina}")
        return

    print(f"    Loading analyzed streets in {opstina}")
    df_anal = pd.read_csv(input_analysis_file, dtype={'ref:RS:ulica': object, 'osm_id': str})
    df_anal = df_anal[pd.notna(df_anal.found_osm_id)]
    df_anal[['total_length', 'average_length', 'total_count_wrong']]  = df_anal.apply(lambda x: calculate_name_match(x), axis=1, result_type='expand')
    df_anal = df_anal[df_anal.total_count_wrong > 0]
    df_anal = df_anal[['rgz_opstina', 'rgz_naselje_mb', 'rgz_naselje', 'rgz_ulica_mb', 'rgz_ulica', 'rgz_way_length', 'conflated_osm_way_length',  'total_length', 'average_length', 'total_count_wrong']]
    df_anal.to_csv(output_path, index=False)
    print(f"    Done name mismatch analysis for opstina {opstina}")
    return df_anal


def do_analysis_geom_missing(opstina, data_path, require_return):
    output_path = os.path.join(data_path, f'qa/geom_missing/{opstina}.csv')
    if not require_return and os.path.exists(output_path):
        print(f"    Skipping {opstina}, already exists")
        return

    input_analysis_file = os.path.join(data_path, f'analysis/{opstina}.csv')
    if not require_return and not os.path.exists(input_analysis_file):
        print(f"    Missing file {input_analysis_file}, cannot process opstina {opstina}")
        return

    print(f"    Loading analyzed streets in {opstina}")
    df_anal = pd.read_csv(input_analysis_file, dtype={'ref:RS:ulica': object, 'osm_id': str})
    df_anal = df_anal[pd.notna(df_anal.conflated_osm_id)]
    df_anal[['geom_missing_need_drawing', 'geom_missing_need_conflate']]  = df_anal.apply(lambda x: calculate_geom_missing(x), axis=1, result_type='expand')
    df_anal = df_anal[(df_anal.geom_missing_need_drawing > 0) | (df_anal.geom_missing_need_conflate > 0)]
    df_anal = df_anal[['rgz_opstina', 'rgz_naselje_mb', 'rgz_naselje', 'rgz_ulica_mb', 'rgz_ulica', 'rgz_way_length', 'conflated_osm_way_length', 'geom_missing_need_conflate', 'geom_missing_need_drawing']]
    df_anal.to_csv(output_path, index=False)
    print(f"    Done geometry missing analysis for opstina {opstina}")
    return df_anal


def process_all_opstina_name_mismatch(data_path, osm_csv_path):
    output_path = os.path.join(data_path, f'qa/name_mismatch.csv')
    if os.path.exists(output_path):
        print(f"    Skipping wrong name analysis, qa/name_mismatch.csv already exists")
        return

    total_csvs = len(os.listdir(osm_csv_path))
    if total_csvs < 168:
        raise Exception("Some or all OSM files missing! Bailing out")

    df_anal = None
    for i, file in enumerate(sorted(os.listdir(osm_csv_path))):
        if not file.endswith(".csv"):
            continue
        opstina = file[:-4]
        print(f"{i + 1}/{total_csvs} Processing {opstina}")
        df_opstina_anal = do_analysis_name_mismatch(opstina, data_path, require_return = True)
        if df_anal is None:
            df_anal = df_opstina_anal
        else:
            df_anal = pd.concat([df_anal, df_opstina_anal])
    df_anal.to_csv(output_path, index=False)


def process_all_opstina_geom_missing(data_path, osm_csv_path):
    output_path = os.path.join(data_path, f'qa/geom_missing.csv')
    if os.path.exists(output_path):
        print(f"    Skipping geometry missing analysis, qa/geom_missing.csv already exists")
        return

    total_csvs = len(os.listdir(osm_csv_path))
    if total_csvs < 168:
        raise Exception("Some or all OSM files missing! Bailing out")

    df_anal = None
    for i, file in enumerate(sorted(os.listdir(osm_csv_path))):
        if not file.endswith(".csv"):
            continue
        opstina = file[:-4]
        print(f"{i + 1}/{total_csvs} Processing {opstina}")
        df_opstina_anal = do_analysis_geom_missing(opstina, data_path, require_return = True)
        if df_anal is None:
            df_anal = df_opstina_anal
        else:
            df_anal = pd.concat([df_anal, df_opstina_anal])
    df_anal.to_csv(output_path, index=False)


def main():
    cwd = os.getcwd()
    data_path = os.path.join(cwd, 'data/')
    rgz_path = os.path.join(data_path, 'rgz/')
    rgz_csv_path = os.path.join(rgz_path, 'csv/')
    osm_csv_path = os.path.join(data_path, 'osm', 'csv')
    output_dir_path_name_mismatch = os.path.join(data_path, 'qa/name_mismatch/')
    output_dir_path_geom_missing = os.path.join(data_path, 'qa/geom_missing/')

    if not os.path.exists(output_dir_path_name_mismatch):
        os.mkdir(output_dir_path_name_mismatch)
    if not os.path.exists(output_dir_path_geom_missing):
        os.mkdir(output_dir_path_geom_missing)

    parser = argparse.ArgumentParser(
        description='create_st_analysis.py - Analyses opstine')
    parser.add_argument('--opstina', default=None, required=False, help='Opstina to process')
    args = parser.parse_args()
    if not args.opstina:
        process_all_opstina_name_mismatch(data_path, osm_csv_path)
        process_all_opstina_geom_missing(data_path, osm_csv_path)
    else:
        if not os.path.exists(os.path.join(rgz_csv_path, f'{normalize_name(args.opstina.lower())}.csv')):
            parser.error(f"File data/rgz/csv/{normalize_name(args.opstina.lower())}.csv do not exist")
            return
        do_analysis_name_mismatch(args.opstina, data_path, require_return = False)
        do_analysis_geom_missing(args.opstina, data_path, require_return=False)


if __name__ == '__main__':
    main()
