# -*- coding: utf-8 -*-
"""Simple settings for reference tags used across scripts.

Defaults can be overridden with environment variables `STREET_REF_TAG`
and `HOUSE_REF_TAG`.
"""
import os

# Default tags (can be overridden via env vars)
STREET_REF_TAG = os.getenv('STREET_REF_TAG', 'ref:HR:ulica')
HOUSE_REF_TAG = os.getenv('HOUSE_REF_TAG', 'ref:HR:kucni_broj')
COUNTRY = os.getenv('COUNTRY', 'croatia')
ENHANCE_WITH_NASELJA = os.getenv('ENHANCE_WITH_NASELJA', 'false')
OPSTINE_DATA_TYPE = os.getenv('OPSTINE_DATA_TYPE', 'csv')  # 'geojson' or 'csv'
COORDINATE_SYSTEM = os.getenv('COORDINATE_SYSTEM', 'EPSG:3035') # or EPSG:32634
CENTER_COORDINATES = '44.5, 17'
SW_COORDINATES = '42, 13.5'
NE_COORDINATES = '46.5, 20'

def get_settings():
    return {
        'STREET_REF_TAG': STREET_REF_TAG,
        'HOUSE_REF_TAG': HOUSE_REF_TAG,
        'COUNTRY': COUNTRY,
        'ENHANCE_WITH_NASELJA': ENHANCE_WITH_NASELJA,
        'OPSTINE_DATA_TYPE': OPSTINE_DATA_TYPE,
        'COORDINATE_SYSTEM': COORDINATE_SYSTEM,
        'CENTER_COORDINATES': CENTER_COORDINATES,
        'SW_COORDINATES': SW_COORDINATES,
        'NE_COORDINATES': NE_COORDINATES
    }
