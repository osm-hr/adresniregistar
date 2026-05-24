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
USE_PLACE_TAG = True
USE_POSTAL_CODE_TAG = False
OPSTINE_DATA_TYPE = os.getenv('OPSTINE_DATA_TYPE', 'csv')  # 'geojson' or 'csv'
COORDINATE_SYSTEM = os.getenv('COORDINATE_SYSTEM', 'EPSG:3035') # or EPSG:32634
CENTER_COORDINATES = '44.5, 17'
SW_COORDINATES = '42, 13.5'
NE_COORDINATES = '47, 20'
WEB_URL = 'dina.osm-hr.org'
CHANGESET_COMMENT_REF = 'DGU address import (updating {settings.HOUSE_REF_TAG} after cadastre refresh), https://c.osm.org/t/137215'
CHANGESET_COMMENT = 'DGU address import (updating street and housenumber after cadastre refresh), https://c.osm.org/t/137215'
CHANGESET_TAGS = "comment=DGU address import (updating street and housenumber)|import=yes|source=DGU_AR|source:url=https://dina.osm-hr.org|import:page=https://wiki.openstreetmap.org/wiki/Croatia/Import_addresses"
CHANGESET_SOURCE = 'DGU_AR'
CADASTRE_AUTHORITY_ABBR = 'DGU'
RUN_DECAPITALIZE_NAMES = False



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
        'WEB_URL': WEB_URL,
        'CHANGESET_COMMENT_REF': CHANGESET_COMMENT_REF,
        'CHANGESET_COMMENT': CHANGESET_COMMENT,
        'CHANGESET_TAGS': CHANGESET_TAGS,
        'CHANGESET_SOURCE': CHANGESET_SOURCE,
        'CADASTRE_AUTHORITY_ABBR': CADASTRE_AUTHORITY_ABBR,
        'USE_POSTAL_CODE_TAG': USE_POSTAL_CODE_TAG,
        'RUN_DECAPITALIZE_NAMES': RUN_DECAPITALIZE_NAMES,
    }
