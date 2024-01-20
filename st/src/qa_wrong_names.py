# -*- coding: utf-8 -*-

import os

import Levenshtein
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import wkt

from common import cyr2lat_small, cyr2intname
from street_mapping import StreetMapping


def is_wrong_name_sr(rgz_proper_name, osm_name, osm_name_sr):
    if pd.isna(osm_name_sr) or osm_name_sr == '':
        # Nothing in name:sr, cannot be wrong
        return False

    if pd.notna(rgz_proper_name) and rgz_proper_name != '':
        # We have proper name, use that to compare to name:sr
        return rgz_proper_name != osm_name_sr
    else:
        if pd.notna(osm_name) and osm_name != '':
            # We have "name" tag
            return osm_name != osm_name_sr
        else:
            # We don't have RGZ name, nor "name" tag, nothing can be wrong
            return False


def is_wrong_name_sr_latn(rgz_proper_name, osm_name, osm_name_sr_latn):
    if pd.isna(osm_name_sr_latn) or osm_name_sr_latn == '':
        # Nothing in name:sr-Latn, cannot be wrong
        return False

    if pd.notna(rgz_proper_name) and rgz_proper_name != '':
        # We have proper name, use that to compare to name:sr-Latn
        return cyr2lat_small(rgz_proper_name) != osm_name_sr_latn
    else:
        if pd.notna(osm_name) and osm_name != '':
            # We have "name" tag, compare with it
            return cyr2lat_small(osm_name) != osm_name_sr_latn
        else:
            # We don't have RGZ name, nor "name" tag, nothing can be wrong
            return False


def is_suspicious_name_en(rgz_proper_name, osm_name, osm_name_en):
    """
    True if there `name:en` tag that is completely different from `name` tag.
    Not wrong per se, but needs to be checked.
    """
    if pd.isna(osm_name_en) or osm_name_en == '':
        # Nothing in name:en, cannot be suspicious
        return False
    if pd.isna(osm_name) or osm_name == '':
        # We don't have "name" tag, cannot compare with name:en
        return False

    # We have "name" tag, compare with it
    ratio_to_latin_name = Levenshtein.ratio(cyr2lat_small(osm_name), osm_name_en)
    ratio_to_int_name = Levenshtein.ratio(cyr2intname(osm_name), osm_name_en)
    return min(ratio_to_latin_name, ratio_to_int_name) < 0.7


def is_unneeded_name_en(rgz_proper_name, osm_name, osm_name_en):
    """
    True if there is `name:en` which is equal of similar to latin version of `name` tag
    """
    if pd.isna(osm_name_en) or osm_name_en == '':
        # Nothing in name:en, cannot be unneeded
        return False
    if pd.isna(osm_name) or osm_name == '':
        # We don't have "name" tag, cannot compare with name:en
        return False

    # We have "name" tag, compare with it
    ratio_to_latin_name = Levenshtein.ratio(cyr2lat_small(osm_name), osm_name_en)
    ratio_to_int_name = Levenshtein.ratio(cyr2intname(osm_name), osm_name_en)
    return max(ratio_to_latin_name, ratio_to_int_name) > 0.9


def is_wrong_int_name(rgz_proper_name, osm_name, osm_int_name):
    if pd.isna(osm_int_name) or osm_int_name == '':
        # Nothing in int_name, cannot be wrong
        return False

    if pd.notna(rgz_proper_name) and rgz_proper_name != '':
        # We have proper name, use that to compare to int_name
        return cyr2intname(rgz_proper_name) != osm_int_name
    else:
        if pd.notna(osm_name) and osm_name != '':
            # We have "name" tag, compare with it
            return cyr2intname(osm_name) != osm_int_name
        else:
            # We don't have RGZ name, nor "name" tag, nothing can be wrong
            return False


def find_wrong_names(cwd, street_mappings: StreetMapping):
    osm_path = os.path.join(cwd, 'data/osm')
    rgz_path = os.path.join(cwd, 'data/rgz')
    qa_path = os.path.join(cwd, 'data/qa')

    if os.path.exists(os.path.join(qa_path, 'wrong_street_names.csv')):
        print("qa/wrong_street_names.csv already exists")
        return

    df_opstine = pd.read_csv(os.path.join(rgz_path, 'opstina.csv'))
    df_opstine['geometry'] = df_opstine.wkt.apply(wkt.loads)
    gdf_opstine = gpd.GeoDataFrame(df_opstine, geometry='geometry', crs="EPSG:32634")
    gdf_opstine.to_crs("EPSG:4326", inplace=True)
    gdf_opstine.sindex
    print(f"Loaded all opstine geometries ({len(gdf_opstine)})")

    df_osm_streets = pd.read_csv(os.path.join(osm_path, 'streets.csv'))
    df_osm_streets['geometry'] = df_osm_streets.osm_geometry.apply(wkt.loads)
    gdf_osm_streets = gpd.GeoDataFrame(df_osm_streets, geometry='geometry', crs="EPSG:4326")
    gdf_osm_streets['ref:RS:ulica'] = gdf_osm_streets['ref:RS:ulica'].astype('Int64').astype('str')
    gdf_osm_streets.sindex
    print(f"Loaded all {len(gdf_osm_streets)} OSM streets")

    df_rgz_streets = pd.read_csv(os.path.join(rgz_path, 'streets.csv'))
    df_rgz_streets['rgz_ulica_mb'] = df_rgz_streets['rgz_ulica_mb'].astype('str')
    print(f"Loaded all {len(df_rgz_streets)} RGZ streets")

    streets_per_opstina = gdf_osm_streets.sjoin(gdf_opstine, how='inner', predicate='intersects')
    streets_per_opstina.sindex

    streets_per_opstina.drop(['index_right', 'opstina_maticni_broj', 'opstina_povrsina', 'okrug_sifra',
                              'okrug_ime', 'okrug_imel', 'wkt'], inplace=True, axis=1)
    print("Split all addresses per opstina")

    # For testing purposes, save and load addresses_per_opstina like this
    # pd.DataFrame(streets_per_opstina).to_csv('~/src/adresniregistar/st/data/addresses_per_opstina.csv', index=False)
    # streets_per_opstina = pd.read_csv('~/src/adresniregistar/st/data/addresses_per_opstina.csv')
    # streets_per_opstina['osm_geometry'] = streets_per_opstina.osm_geometry.apply(wkt.loads)
    # streets_per_opstina = gpd.GeoDataFrame(streets_per_opstina, geometry='osm_geometry', crs="EPSG:4326")
    # import ast
    # streets_per_opstina['tags'] = streets_per_opstina.apply(lambda row: ast.literal_eval(row.tags), axis=1)
    # streets_per_opstina['ref:RS:ulica'] = streets_per_opstina['ref:RS:ulica'].astype('str')
    # streets_per_opstina.sindex

    # Merge with RGZ streets and find out proper street names
    streets_per_opstina = streets_per_opstina.merge(df_rgz_streets[['rgz_opstina', 'rgz_ulica_mb', 'rgz_ulica']], how='left', left_on='ref:RS:ulica', right_on='rgz_ulica_mb')
    streets_per_opstina['rgz_ulica_proper'] = streets_per_opstina[['rgz_ulica', 'rgz_opstina']].apply(
        lambda x: street_mappings.get_name(x['rgz_ulica'], x['rgz_opstina'], default_value='') if pd.notna(x['rgz_ulica']) and x['rgz_ulica'] != '' else np.nan, axis=1)

    # Detect all wrong tags
    streets_per_opstina['wrong_name'] = streets_per_opstina[['rgz_ulica_proper', 'osm_name']].apply(
        lambda x: pd.notna(x['osm_name']) and pd.notna(x['rgz_ulica_proper']) and x['osm_name'] != '' and x['rgz_ulica_proper'] != '' and x['rgz_ulica_proper'] != x['osm_name'], axis=1)
    streets_per_opstina['missing_name'] = streets_per_opstina[['rgz_ulica_proper', 'osm_name']].apply(
        lambda x: pd.notna(x['rgz_ulica_proper']) and x['rgz_ulica_proper'] != '' and (pd.isna(x['osm_name']) or x['osm_name'] == ''), axis=1)

    streets_per_opstina['wrong_name_sr'] = streets_per_opstina[['rgz_ulica_proper', 'osm_name', 'osm_name_sr']].apply(
        lambda x: is_wrong_name_sr(x['rgz_ulica_proper'], x['osm_name'], x['osm_name_sr']), axis=1)
    streets_per_opstina['missing_name_sr'] = streets_per_opstina[['osm_name', 'osm_name_sr']].apply(
        lambda x: pd.notna(x['osm_name']) and (pd.isna(x['osm_name_sr']) or x['osm_name_sr'] == '') , axis=1)

    streets_per_opstina['wrong_name_sr_latn'] = streets_per_opstina[['rgz_ulica_proper', 'osm_name', 'osm_name_sr_latn']].apply(
        lambda x: is_wrong_name_sr_latn(x['rgz_ulica_proper'], x['osm_name'], x['osm_name_sr_latn']), axis=1)
    streets_per_opstina['missing_name_sr_latn'] = streets_per_opstina[['osm_name', 'osm_name_sr_latn']].apply(
        lambda x: pd.notna(x['osm_name']) and x['osm_name'] != '' and (pd.isna(x['osm_name_sr_latn']) or x['osm_name_sr_latn'] == ''), axis=1)

    streets_per_opstina['suspicious_name_en'] = streets_per_opstina[['rgz_ulica_proper', 'osm_name', 'osm_name_en']].apply(
        lambda x: is_suspicious_name_en(x['rgz_ulica_proper'], x['osm_name'], x['osm_name_en']), axis=1)
    streets_per_opstina['unneeded_name_en'] = streets_per_opstina[['rgz_ulica_proper', 'osm_name', 'osm_name_en']].apply(
        lambda x: is_unneeded_name_en(x['rgz_ulica_proper'], x['osm_name'], x['osm_name_en']), axis=1)

    streets_per_opstina['wrong_int_name'] = streets_per_opstina[['rgz_ulica_proper', 'osm_name', 'osm_int_name']].apply(
        lambda x: is_wrong_int_name(x['rgz_ulica_proper'], x['osm_name'], x['osm_int_name']), axis=1)
    streets_per_opstina['missing_int_name'] = streets_per_opstina[['osm_name', 'osm_int_name']].apply(
        lambda x: pd.notna(x['osm_name']) and x['osm_name'] != '' and (pd.isna(x['osm_int_name']) or x['osm_int_name'] == ''), axis=1)

    streets_per_opstina = streets_per_opstina[
        streets_per_opstina.wrong_name | streets_per_opstina.missing_name |
        streets_per_opstina.wrong_name_sr | streets_per_opstina.missing_name_sr |
        streets_per_opstina.wrong_name_sr_latn | streets_per_opstina.missing_name_sr_latn |
        streets_per_opstina.unneeded_name_en |
        streets_per_opstina.wrong_int_name | streets_per_opstina.missing_int_name
    ]
    pd.DataFrame(streets_per_opstina).to_csv(os.path.join(qa_path, 'wrong_street_names.csv'), index=False)
    print("Created wrong_street_names.csv")


def main():
    cwd = os.getcwd()

    street_mappings = StreetMapping(os.path.join(cwd, '..', 'ar'))

    find_wrong_names(cwd, street_mappings)


if __name__ == '__main__':
    main()
