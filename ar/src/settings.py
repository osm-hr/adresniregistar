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
OPSTINE_DATA_TYPE = os.getenv('OPSTINE_DATA_TYPE', 'geojson')  # or 'csv'

def get_settings():
    return {
        'STREET_REF_TAG': STREET_REF_TAG,
        'HOUSE_REF_TAG': HOUSE_REF_TAG,
        'COUNTRY': COUNTRY,
        'ENHANCE_WITH_NASELJA': ENHANCE_WITH_NASELJA,
        'OPSTINE_DATA_TYPE': OPSTINE_DATA_TYPE
    }
