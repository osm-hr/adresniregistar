# -*- coding: utf-8 -*-

import os

import Levenshtein
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import wkt

from common import cyr2lat, cyr2lat_small, cyr2intname
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


def is_needed_int_name(rgz_proper_name, osm_name, osm_int_name):
    if pd.notna(osm_int_name) and osm_int_name != '':
        # int_name exists, no need for it
        return False

    matches = ["ш", "ч", "ћ", "ж", "ђ", "Ш", "Ч", "Ћ", "Ж", "Ђ"]

    if pd.notna(rgz_proper_name) and rgz_proper_name != '':
        if any(x in rgz_proper_name for x in matches):
            return True
    elif pd.notna(osm_name) and osm_name != '':
        # We have "name" tag, compare with it
        if any(x in osm_name for x in matches):
            return True
    return False


def is_month_in_name(s: str):
    months = ['јануар', 'фебруар', 'март', 'април', 'мај', 'јун', 'јул', 'август', 'септемб', 'октоб', 'новемб', 'децемб']
    found_month = False

    for month in months:
        if month in s:
            found_month = True
            break
    return found_month


def extract_number(s: str):
    number = ''
    is_ordinal = False
    in_number = False
    for c in s:
        if c.isdigit():
            if in_number:
                number = number + c
            else:
                in_number = True
                number = c
        else:
            if in_number:
                is_ordinal = c == '.'
                break
    if number == '':
        return False, -1, False
    else:
        return True, int(number), is_ordinal


ordinal_replacements = [
    ('први', '1.', 'I'),
    ('прва', '1.', 'I'),
    ('првe', '1.', 'I'),
    ('прво', '1.', 'I'),
    ('други', '2.', 'II'),
    ('друга', '2.', 'II'),
    ('друге', '2.', 'II'),
    ('друго', '2.', 'II'),
    ('трећи', '3.', 'III'),
    ('трећа', '3.', 'III'),
    ('треће', '3.', 'III'),
    ('четврти', '4.', 'IV'),
    ('четврта', '4.', 'IV'),
    ('четврте', '4.', 'IV'),
    ('четврто', '4.', 'IV'),
    ('пети', '5.', 'V'),
    ('пета', '5.', 'V'),
    ('пете', '5.', 'V'),
    ('пето', '5.', 'V'),
    ('шести', '6.', 'VI'),
    ('шеста', '6.', 'VI'),
    ('шесте', '6.', 'VI'),
    ('шесто', '6.', 'VI'),
    ('седми', '7.', 'VII'),
    ('седма', '7.', 'VII'),
    ('седме', '7.', 'VII'),
    ('седмо', '7.', 'VII'),
    ('осми', '8.', 'VIII'),
    ('осма', '8.', 'VIII'),
    ('осме', '8.', 'VIII'),
    ('осмо', '8.', 'VIII'),
    ('девети', '9.', 'IX'),
    ('девета', '9.', 'IX'),
    ('девете', '9.', 'IX'),
    ('девето', '9.', 'IX'),
    ('десети', '10.', 'X'),
    ('десета', '10.', 'X'),
    ('десете', '10.', 'X'),
    ('десето', '10.', 'X'),
]

ordinal_replacements_latn = []
for ordinal_replacement in ordinal_replacements:
    ordinal_replacements_latn.append((cyr2lat(ordinal_replacement[0]), ordinal_replacement[1], ordinal_replacement[2]))

titles_replacements = [
    ('првог', 'I'),
    ('првога', 'I'),
    ('другог', 'II'),
    ('другога', 'II'),
    ('трећег', 'III'),
    ('трећега', 'III'),
    ('четвртог', 'IV'),
    ('четвртога', 'IV'),
    ('петог', 'V'),
    ('петога', 'V'),
    ('шестог', 'VI'),
    ('шестога', 'VI'),
    ('седмог', 'VII'),
    ('седмога', 'VII'),
    ('осмог', 'VIII'),
    ('осмога', 'VIII'),
    ('деветог', 'IX'),
    ('деветога', 'IX'),
    ('десетог', 'X'),
    ('десетога', 'X'),
]

titles_replacements_latn = []
for titles_replacement in titles_replacements:
    titles_replacements_latn.append((cyr2lat(titles_replacement[0]), titles_replacement[1]))

number_replacements = [
    ('један', '1'),
    ('два', '2'),
    ('три', '3'),
    ('четири', '4'),
    ('пет', '5'),
    ('шест', '6'),
    ('седам', '7'),
    ('осам', '8'),
    ('девет', '9'),
    ('десет', '10'),
]

number_replacements_latn = []
for number_replacement in number_replacements:
    number_replacements_latn.append((cyr2lat(number_replacement[0]), number_replacement[1]))


def check_alt_name(rgz_proper_name, osm_name, alt_name, is_latin: bool = False):
    """
    Returns (is_missing: bool, is_wrong: bool, suggested_alt_name: str, is_partial: bool)
    is_missing is False if it is determined that alt_name is missing (or cannot be determined, or there is alt_name), True if there is
    is_wrong is False if it is determined that alt_name is not wrong (or cannot be determined, or there is no alt_name), True if there is
    proper_alt_name is suggestion or partial suggestion for proper alt_name. Empty string means there is no suggestion
    is_partial is False if proper_alt_name can be determined and is proper alt_name. True if this is just a part of alt_name that was expected and is missing
    """
    is_alt_name_missing = pd.isna(alt_name)

    if pd.notna(rgz_proper_name):
        name_to_check = rgz_proper_name
    elif pd.notna(osm_name):
        name_to_check = osm_name
    else:
        # There is no RGZ name, nor "name" tag, bail out
        return False, False, '', False
    name_to_check_lower = name_to_check.lower()

    # Check for ordinal numbers
    ordinal_replacement_to_use = ordinal_replacements if not is_latin else ordinal_replacements_latn
    for replacement in ordinal_replacement_to_use:
        needle = replacement[0]
        roman = replacement[2]
        if not is_alt_name_missing and roman.lower() in alt_name:
            continue
        if ' ' + needle + ' ' in name_to_check_lower:
            idx = name_to_check_lower.find(needle)
            proper_alt_name = name_to_check[0:idx-1] + ' ' + replacement[1] + ' ' + name_to_check[idx + len(needle) + 1:]
            if is_alt_name_missing or alt_name != proper_alt_name:
                return is_alt_name_missing, not is_alt_name_missing, proper_alt_name, False
        if name_to_check_lower.startswith(needle + ' '):
            proper_alt_name = replacement[1] + ' ' + name_to_check[len(needle) + 1:]
            if is_alt_name_missing or alt_name != proper_alt_name:
                return is_alt_name_missing, not is_alt_name_missing, proper_alt_name, False
        if name_to_check_lower.endswith(' ' + needle):
            idx = name_to_check_lower.find(needle)
            proper_alt_name = name_to_check[0:idx - 1] + ' ' + replacement[1]
            if is_alt_name_missing or alt_name != proper_alt_name:
                return is_alt_name_missing, not is_alt_name_missing, proper_alt_name, False

    # check for ordinal numbers, looking like some king titles, those are certainly roman numerals
    # exception is if they are coming from month numbers
    titles_replacements_to_use = titles_replacements if not is_latin else titles_replacements_latn
    for replacement in titles_replacements_to_use:
        needle = replacement[0]
        if ' ' + needle + ' ' in name_to_check_lower:
            if is_month_in_name(name_to_check_lower):
                continue
            idx = name_to_check_lower.find(needle)
            proper_alt_name = name_to_check[0:idx-1] + ' ' + replacement[1] + ' ' + name_to_check[idx + len(needle) + 1:]
            if is_alt_name_missing or alt_name != proper_alt_name:
                return is_alt_name_missing, not is_alt_name_missing, proper_alt_name, False
        if name_to_check_lower.startswith(needle + ' '):
            if is_month_in_name(name_to_check_lower):
                continue
            proper_alt_name = replacement[1] + ' ' + name_to_check[len(needle) + 1:]
            if is_alt_name_missing or alt_name != proper_alt_name:
                return is_alt_name_missing, not is_alt_name_missing, proper_alt_name, False
        if name_to_check_lower.endswith(' ' + needle):
            if is_month_in_name(name_to_check_lower):
                continue
            idx = name_to_check_lower.find(needle)
            proper_alt_name = name_to_check[0:idx - 1] + ' ' + replacement[1]
            if is_alt_name_missing or alt_name != proper_alt_name:
                return is_alt_name_missing, not is_alt_name_missing, proper_alt_name, False

    # check for regular numbers
    number_replacements_to_use = number_replacements if not is_latin else number_replacements_latn
    for replacement in number_replacements_to_use:
        needle = replacement[0]
        if ' ' + needle + ' ' in name_to_check_lower:
            idx = name_to_check_lower.find(needle)
            proper_alt_name = name_to_check[0:idx-1] + ' ' + replacement[1] + ' ' + name_to_check[idx + len(needle) + 1:]
            if is_alt_name_missing or alt_name != proper_alt_name:
                return is_alt_name_missing, not is_alt_name_missing, proper_alt_name, False
        if name_to_check_lower.startswith(needle + ' '):
            proper_alt_name = replacement[1] + ' ' + name_to_check[len(needle) + 1:]
            if is_alt_name_missing or alt_name != proper_alt_name:
                return is_alt_name_missing, not is_alt_name_missing, proper_alt_name, False
        if name_to_check_lower.endswith(' ' + needle):
            idx = name_to_check_lower.find(needle)
            proper_alt_name = name_to_check[0:idx - 1] + ' ' + replacement[1]
            if is_alt_name_missing or alt_name != proper_alt_name:
                return is_alt_name_missing, not is_alt_name_missing, proper_alt_name, False

    # check for numbers to convert to written form
    has_number, number, is_ordinal = extract_number(name_to_check_lower)
    while True:
        if not has_number:
            break
        contains_roman = not is_alt_name_missing and number <= 10 and (
                titles_replacements_to_use[number * 2 - 2][1] in alt_name or
                titles_replacements_to_use[number * 2 - 1][1] in alt_name)
        if contains_roman:
            break

        possibilities = []
        if is_ordinal:
            for ordinal_replacement in ordinal_replacement_to_use:
                if ordinal_replacement[1] == str(number) + '.':
                    possibilities.append(ordinal_replacement[0])
            if number < 10:
                possibilities.append(titles_replacements_to_use[number * 2 - 2][0])
                possibilities.append(titles_replacements_to_use[number * 2 - 1][0])
        else:
            for number_replacement in number_replacements_to_use:
                if number_replacement[1] == str(number):
                    possibilities.append(number_replacement[0])
        found_possibility = False
        if not is_alt_name_missing:
            for possibility in possibilities:
                if possibility in alt_name.lower():
                    found_possibility = True
                    break
        if not found_possibility and len(possibilities) > 0:
            idx = name_to_check_lower.find(str(number) + ('.' if is_ordinal else ''))
            proper_alt_name = name_to_check[0:idx] + '~~' + possibilities[0] + '~~' + name_to_check[idx + len(str(number)) + 1:]
            return is_alt_name_missing, not is_alt_name_missing, proper_alt_name, True
        break

    # check for doktora
    doctor = 'доктора' if not is_latin else 'doktora'
    if ' ' + doctor + ' ' in name_to_check_lower:
        idx = name_to_check_lower.find(doctor)
        proper_alt_name = name_to_check[0:idx-1] + (' др ' if not is_latin else ' dr ') + name_to_check[idx + len(doctor) + 1:]
        if not has_number and (is_alt_name_missing or alt_name != proper_alt_name):
            return is_alt_name_missing, not is_alt_name_missing, proper_alt_name, False
    if name_to_check_lower.startswith(doctor + ' '):
        proper_alt_name = ('Др ' if not is_latin else 'Dr ') + name_to_check[len(doctor) + 1:]
        if not has_number and (is_alt_name_missing or alt_name != proper_alt_name):
            return is_alt_name_missing, not is_alt_name_missing, proper_alt_name, False
    if name_to_check_lower.endswith(' ' + doctor):
        idx = name_to_check_lower.find(doctor)
        proper_alt_name = name_to_check[0:idx - 1] + (' др' if not is_latin else ' dr')
        if not has_number and (is_alt_name_missing or alt_name != proper_alt_name):
            return is_alt_name_missing, not is_alt_name_missing, proper_alt_name, False

    return False, False, '', False


def find_wrong_names(cwd, street_mappings: StreetMapping):
    osm_path = os.path.join(cwd, 'data/osm')
    rgz_path = os.path.join(cwd, 'data/rgz')
    qa_path = os.path.join(cwd, 'data/qa')

    if os.path.exists(os.path.join(qa_path, 'wrong_street_names.csv')) and os.path.exists(os.path.join(qa_path, 'wrong_alt_names.csv')):
        print("qa/wrong_street_names.csv and qa/wrong_alt_names.csv already exist")
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

    # Merge with RGZ streets and find out proper street names
    streets_per_opstina = streets_per_opstina.merge(df_rgz_streets[['rgz_opstina', 'rgz_ulica_mb', 'rgz_ulica']], how='left', left_on='ref:RS:ulica', right_on='rgz_ulica_mb')
    streets_per_opstina['rgz_ulica_proper'] = streets_per_opstina[['rgz_ulica', 'rgz_ulica_mb']].apply(
        lambda x: street_mappings.get_name(x['rgz_ulica'], x['rgz_ulica_mb'], default_value='') if pd.notna(x['rgz_ulica']) and x['rgz_ulica'] != '' else np.nan, axis=1)

    # For testing purposes, save and load addresses_per_opstina like this
    # pd.DataFrame(streets_per_opstina).to_csv('~/src/adresniregistar/st/data/qa/addresses_per_opstina.csv', index=False)
    # streets_per_opstina = pd.read_csv('~/src/adresniregistar/st/data/qa/addresses_per_opstina.csv')
    # streets_per_opstina['ref:RS:ulica'] = streets_per_opstina['ref:RS:ulica'].astype('str')

    if not os.path.exists(os.path.join(qa_path, 'wrong_street_names.csv')):
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
        streets_per_opstina['missing_int_name'] = streets_per_opstina[['rgz_ulica_proper', 'osm_name', 'osm_int_name']].apply(
            lambda x: is_needed_int_name(x['rgz_ulica_proper'], x['osm_name'], x['osm_int_name']), axis=1)

        streets_per_opstina_wrong_names = streets_per_opstina[
            streets_per_opstina.wrong_name | streets_per_opstina.missing_name |
            streets_per_opstina.wrong_name_sr | streets_per_opstina.missing_name_sr |
            streets_per_opstina.wrong_name_sr_latn | streets_per_opstina.missing_name_sr_latn |
            streets_per_opstina.unneeded_name_en |
            streets_per_opstina.wrong_int_name | streets_per_opstina.missing_int_name
        ]
        streets_per_opstina_wrong_names = streets_per_opstina_wrong_names.sort_values(['osm_id', 'opstina_imel'])
        pd.DataFrame(streets_per_opstina_wrong_names).to_csv(os.path.join(qa_path, 'wrong_street_names.csv'), index=False)
        print("Created wrong_street_names.csv")

    if not os.path.exists(os.path.join(qa_path, 'wrong_alt_names.csv')):
        streets_per_opstina[['is_missing_alt_name', 'is_wrong_alt_name', 'alt_name_suggestion', 'is_alt_name_suggestion_partial']] = \
            streets_per_opstina[['rgz_ulica_proper', 'osm_name', 'osm_alt_name']].apply(
                lambda x: check_alt_name(x['rgz_ulica_proper'], x['osm_name'], x['osm_alt_name']), axis=1, result_type='expand')
        streets_per_opstina[['is_missing_alt_name_sr', 'is_wrong_alt_name_sr', 'alt_name_sr_suggestion', 'is_alt_name_sr_suggestion_partial']] = \
            streets_per_opstina[['rgz_ulica_proper', 'osm_name_sr', 'osm_alt_name_sr']].apply(
                lambda x: check_alt_name(x['rgz_ulica_proper'], x['osm_name_sr'], x['osm_alt_name_sr']), axis=1, result_type='expand')
        streets_per_opstina[['is_missing_alt_name_sr_latn', 'is_wrong_alt_name_sr_latn', 'alt_name_sr_latn_suggestion', 'is_alt_name_sr_latn_suggestion_partial']] = \
            streets_per_opstina[['rgz_ulica_proper', 'osm_name_sr_latn', 'osm_alt_name_sr_latn']].apply(
                lambda x: check_alt_name(cyr2lat_small(x['rgz_ulica_proper']) if pd.notna(x['rgz_ulica_proper']) else np.nan, x['osm_name_sr_latn'], x['osm_alt_name_sr_latn'], is_latin=True), axis=1, result_type='expand')

        streets_per_opstina_wrong_alt_names = streets_per_opstina[streets_per_opstina.is_missing_alt_name | streets_per_opstina.is_wrong_alt_name]
        streets_per_opstina_wrong_alt_names = streets_per_opstina_wrong_alt_names[
            ['osm_id', 'osm_name', 'osm_alt_name', 'osm_alt_name_sr', 'osm_alt_name_sr_latn', 'ref:RS:ulica', 'note', 'opstina_imel', 'rgz_ulica_mb', 'rgz_ulica_proper',
             'is_missing_alt_name', 'is_wrong_alt_name', 'alt_name_suggestion', 'is_alt_name_suggestion_partial',
             'is_missing_alt_name_sr', 'is_wrong_alt_name_sr', 'alt_name_sr_suggestion', 'is_alt_name_sr_suggestion_partial',
             'is_missing_alt_name_sr_latn', 'is_wrong_alt_name_sr_latn', 'alt_name_sr_latn_suggestion', 'is_alt_name_sr_latn_suggestion_partial',]
        ]
        streets_per_opstina_wrong_alt_names = streets_per_opstina_wrong_alt_names.sort_values(['osm_id', 'opstina_imel'])
        pd.DataFrame(streets_per_opstina_wrong_alt_names).to_csv(os.path.join(qa_path, 'wrong_alt_names.csv'), index=False)
        print("Created wrong_alt_names.csv")


def main():
    cwd = os.getcwd()
    street_mappings = StreetMapping(os.path.join(cwd, '..', 'ar'))
    find_wrong_names(cwd, street_mappings)


if __name__ == '__main__':
    main()
