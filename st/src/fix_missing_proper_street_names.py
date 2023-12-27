# -*- coding: utf-8 -*-

import os

import pandas as pd

from street_mapping import StreetMapping, best_effort_decapitalize


def main():
    cwd = os.getcwd()
    rgz_path = os.path.join(cwd, 'data/', 'rgz')

    street_mappings = StreetMapping(os.path.join(cwd, '..', 'ar'))

    df_rgz = pd.read_csv(os.path.join(rgz_path, f'streets.new.csv'))
    df_rgz['rgz_ulica_proper'] = df_rgz[['rgz_ulica', 'rgz_opstina']].apply(lambda x: street_mappings.get_name(x['rgz_ulica'], x['rgz_opstina'], default_value='foo'), axis=1)
    df_missing_addresses = df_rgz[df_rgz.rgz_ulica_proper == 'foo']
    df_missing_addresses['best_effort'] = df_missing_addresses['rgz_ulica'].apply(lambda x: best_effort_decapitalize(x))
    pd.DataFrame(df_missing_addresses[['rgz_ulica', 'best_effort']]).to_csv(os.path.join(rgz_path, f'missing_streets.csv'), index=False)
    print("Created missing_streets.csv, fix it and paste it to curated_streets.csv")


if __name__ == '__main__':
    main()
