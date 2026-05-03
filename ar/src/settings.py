# -*- coding: utf-8 -*-
"""Simple settings for reference tags used across scripts.

Defaults can be overridden with environment variables `STREET_REF_TAG`
and `HOUSE_REF_TAG`.
"""
import os

# Default tags (can be overridden via env vars)
STREET_REF_TAG = os.getenv('STREET_REF_TAG', 'ref:RS:ulica')
HOUSE_REF_TAG = os.getenv('HOUSE_REF_TAG', 'ref:RS:kucni_broj')
COUNTRY = os.getenv('COUNTRY', 'serbia')
ENHANCE_WITH_NASELJA = os.getenv('ENHANCE_WITH_NASELJA', 'true')
USE_PLACE_TAG = False
OPSTINE_DATA_TYPE = os.getenv('OPSTINE_DATA_TYPE', 'csv')
COORDINATE_SYSTEM = os.getenv('COORDINATE_SYSTEM', 'EPSG:32634')
CENTER_COORDINATES = '44.5, 21'
SW_COORDINATES = '42, 18.5'
NE_COORDINATES = '46.5, 23.5'
WEB_URL = 'dina.openstreetmap.rs'
CHANGESET_COMMENT_REF = 'RGZ address import (updating {settings.HOUSE_REF_TAG} after cadastre refresh), https://lists.openstreetmap.org/pipermail/imports/2023-March/007187.html'
CHANGESET_COMMENT = 'RGZ address import (updating street and housenumber after cadastre refresh), https://lists.openstreetmap.org/pipermail/imports/2023-March/007187.html'
CHANGESET_SOURCE = 'RGZ_AR'

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
        'NE_COORDINATES': NE_COORDINATES,
        'WEB_URL': WEB_URL
    }
