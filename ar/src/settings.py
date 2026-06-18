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
ADDRESS_CRS = os.getenv('ADDRESS_CRS', 'EPSG:32634')
ADMIN_CRS = os.getenv('ADMIN_CRS', ADDRESS_CRS)
CENTER_COORDINATES = os.getenv('CENTER_COORDINATES', '44.5, 21')
SW_COORDINATES = os.getenv('SW_COORDINATES', '42, 18.5')
NE_COORDINATES = os.getenv('NE_COORDINATES', '46.5, 23.5')
WEB_URL = os.getenv('WEB_URL', 'dina.openstreetmap.rs')
CHANGESET_COMMENT = os.getenv('CHANGESET_COMMENT', 'RGZ address import (updating street and housenumber after cadastre refresh), https://lists.openstreetmap.org/pipermail/imports/2023-March/007187.html')
CHANGESET_SOURCE = os.getenv('CHANGESET_SOURCE', 'RGZ_AR')
IMPORT_PAGE = os.getenv('IMPORT_PAGE', 'https://wiki.openstreetmap.org/wiki/Serbia/RGZ_Import')
SOURCE_URL = os.getenv('SOURCE_URL', 'https://dina.openstreetmap.rs')
CHANGESET_TAGS_JSON = {"comment": CHANGESET_COMMENT, "source": CHANGESET_SOURCE, "import": "yes", "source:url": SOURCE_URL, "import:page": IMPORT_PAGE}
CHANGESET_TAGS_TXT  = f"comment={CHANGESET_COMMENT}|source={CHANGESET_SOURCE}|import=yes|source:url={SOURCE_URL}|import:page={IMPORT_PAGE}"
CADASTRE_AUTHORITY_ABBR = os.getenv('CADASTRE_AUTHORITY_ABBR', 'RGZ')
RUN_DECAPITALIZE_NAMES = os.getenv('RUN_DECAPITALIZE_NAMES', 'false') == 'true'
OSM_USERNAME = os.getenv('OSM_USERNAME')
OSM_PASSWORD = os.getenv('OSM_PASSWORD')
INSPIRE_ADMIN_LEVEL_1_NAME = os.getenv('INSPIRE_ADMIN_LEVEL_1_NAME', 'Jedinica lokalne samouprave')
INSPIRE_ADMIN_LEVEL_2_NAME = os.getenv('INSPIRE_ADMIN_LEVEL_2_NAME','Naselje')
INSPIRE_ADDR_FEED_URL = os.getenv('INSPIRE_ADDR_FEED_URL', 'https://geoportal.dgu.hr/services/atom/ad/xml')
