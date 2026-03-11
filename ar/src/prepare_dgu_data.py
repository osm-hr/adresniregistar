#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
from common import normalize_name

print("Reading data/rgz/addresses.csv...")
df = pd.read_csv('data/rgz/addresses.csv')

print(f"Total rows: {len(df)}")

os.makedirs('data/rgz/csv', exist_ok=True)

used_filenames = set()

for opstina_mb, group in df.groupby('rgz_opstina_mb'):

    if pd.isna(opstina_mb):
        continue

    # Get municipality name (should be identical inside group)
    opstina_name = group['rgz_opstina'].iloc[0]

    if pd.isna(opstina_name):
        print(f"⚠ Skipping MB {opstina_mb} (no name)")
        continue

    # Sanitize filename
    filename = (normalize_name(str(opstina_name).lower()))

    # Detect duplicates
    if filename in used_filenames:
        print(f"❌ Duplicate filename detected: {filename}")
        print(f"   Municipality MB: {opstina_mb}")
        continue

    used_filenames.add(filename)

    output_file = f'data/rgz/csv/{filename}.csv'
    group.to_csv(output_file, index=False)

    print(f"Created {output_file} with {len(group)} addresses")

print(f"Total opstine: {len(used_filenames)}")