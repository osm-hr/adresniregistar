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
ENHANCE_WITH_NASELJA = os.getenv('ENHANCE_WITH_NASELJA', 'true') == 'true'
USE_PLACE_TAG = os.getenv('USE_PLACE_TAG', 'false') == 'true'
USE_POSTAL_CODE_TAG = os.getenv('USE_POSTAL_CODE_TAG', 'false') == 'true'
COORDINATE_SYSTEM = os.getenv('COORDINATE_SYSTEM', 'EPSG:32634')
CENTER_COORDINATES = os.getenv('CENTER_COORDINATES', '44.5, 21')
SW_COORDINATES = os.getenv('SW_COORDINATES', '42, 18.5')
NE_COORDINATES = os.getenv('NE_COORDINATES', '46.5, 23.5')
WEB_URL = os.getenv('WEB_URL', 'dina.openstreetmap.rs')
CHANGESET_COMMENT = 'RGZ address import (updating street and housenumber after cadastre refresh), https://lists.openstreetmap.org/pipermail/imports/2023-March/007187.html'
CHANGESET_SOURCE = 'RGZ_AR'
IMPORT_PAGE = 'https://wiki.openstreetmap.org/wiki/Serbia/RGZ_Import'
SOURCE_URL = 'https://dina.openstreetmap.rs'
CHANGESET_TAGS_JSON = {"comment": CHANGESET_COMMENT, "source": CHANGESET_SOURCE, "import": "yes", "source:url": SOURCE_URL, "import:page": IMPORT_PAGE}
CHANGESET_TAGS_TXT  = f"comment={CHANGESET_COMMENT}|source={CHANGESET_SOURCE}|import=yes|source:url={SOURCE_URL}|import:page={IMPORT_PAGE}"
CADASTRE_AUTHORITY_ABBR = os.getenv('CADASTRE_AUTHORITY_ABBR', 'RGZ')
RUN_DECAPITALIZE_NAMES = os.getenv('RUN_DECAPITALIZE_NAMES', 'false') == 'true'
OSM_USERNAME = os.getenv('OSM_USERNAME')
OSM_PASSWORD = os.getenv('OSM_PASSWORD')

def get_settings():
    return {
        'STREET_REF_TAG': STREET_REF_TAG,
        'HOUSE_REF_TAG': HOUSE_REF_TAG,
        'COUNTRY': COUNTRY,
        'ENHANCE_WITH_NASELJA': ENHANCE_WITH_NASELJA,
        'COORDINATE_SYSTEM': COORDINATE_SYSTEM,
        'CENTER_COORDINATES': CENTER_COORDINATES,
        'SW_COORDINATES': SW_COORDINATES,
        'NE_COORDINATES': NE_COORDINATES,
        'WEB_URL': WEB_URL,
        'CHANGESET_COMMENT': CHANGESET_COMMENT,
        'CHANGESET_SOURCE': CHANGESET_SOURCE,
        'CHANGESET_TAGS_JSON': CHANGESET_TAGS_JSON,
        'CHANGESET_TAGS_TXT': CHANGESET_TAGS_TXT,
        'CADASTRE_AUTHORITY_ABBR': CADASTRE_AUTHORITY_ABBR,
        'USE_POSTAL_CODE_TAG': USE_POSTAL_CODE_TAG,
        'RUN_DECAPITALIZE_NAMES': RUN_DECAPITALIZE_NAMES,
        'OSM_USERNAME': OSM_USERNAME,
        'OSM_PASSWORD': OSM_PASSWORD
    }
