#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

import pandas as pd

from street_mapping import StreetMapping


def main():
    addresses_path = 'data/rgz/addresses.csv'
    temp_path = addresses_path + '.tmp'

    street_mappings = StreetMapping(os.getcwd())

    # All columns stay strings so that rewriting the file does not alter ids or house numbers
    df = pd.read_csv(addresses_path, dtype=str, keep_default_na=False)

    streets = df[['rgz_ulica', 'rgz_ulica_mb']].drop_duplicates()
    names = {
        (rgz_ulica, ulica_id): street_mappings.get_name(rgz_ulica, ulica_id)
        for rgz_ulica, ulica_id in zip(streets['rgz_ulica'], streets['rgz_ulica_mb'])
    }
    df['rgz_ulica_osm_name'] = [names[street] for street in zip(df['rgz_ulica'], df['rgz_ulica_mb'])]

    df.to_csv(temp_path, index=False, encoding='utf-8')
    os.replace(temp_path, addresses_path)

    print(f"addresses.csv: street names added for {len(df)} addresses")


if __name__ == '__main__':
    main()
