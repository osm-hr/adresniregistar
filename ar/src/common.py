# -*- coding: utf-8 -*-

import csv
import json
import math
import os
from enum import Enum

import osmium
from shapely import geometry

OPSTINE_TO_SKIP = ['VITINA', 'VUČITRN', 'GLOGOVAC', 'GNJILANE', 'GORA', 'DEČANI', 'ĐAKOVICA',
                   'ZVEČAN', 'ZUBIN POTOK', 'ISTOK', 'KAČANIK', 'KLINA', 'KOSOVSKA MITROVICA',
                   'KOSOVO POLJE', 'KOSOVSKA KAMENICA', 'LEPOSAVIĆ', 'LIPLJAN', 'NOVO BRDO',
                   'OBILIĆ', 'ORAHOVAC', 'PEĆ', 'PODUJEVO', 'PRIŠTINA', 'PRIZREN', 'SRBICA',
                   'SUVA REKA', 'UROŠEVAC', 'ŠTIMLJE', 'ŠTRPCE']


class AddressInBuildingResolution(Enum):
    # Everything is fine, no action needed. Used internally, user should not see this
    NO_ACTION = 1
    # Case where there is single POI and we think POI can be moved to building way
    # If street or housenumber on POI is null, take it from building
    MERGE_POI_TO_BUILDING = 2
    # Case where there is/are address(es) and we think it can be moved to building way.
    # If street or housenumber on address is null, take it from building
    MERGE_ADDRESS_TO_BUILDING = 3
    # Case where we don't move POI(s) to building, but there is single address and it can be copied to building way too
    COPY_POI_ADDRESS_TO_BUILDING = 4
    # There are multiple addresses and they should be attached to building way
    ATTACH_ADDRESSES_TO_BUILDING = 5
    # There are already different addresses in nodes, no need for address in building
    REMOVE_ADDRESS_FROM_BUILDING = 6
    # Addresses in building and in POIs/nodes do not match, need human to resolve manually
    ADDRESSES_NOT_MATCHING = 7
    # There are too many POIs and/or simple addresses inside one building to create meaningful resolution, human need to take a look
    CASE_TOO_COMPLEX = 8
    # Building is not a building at all, it is a node wih building tag, tag should be removed
    BUILDING_IS_NODE = 9
    # Either building or addresses/POIs have "note" tag and are eligable for any changes
    NOTE_PRESENT = 10


normalize_rules = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e',
    'ж': 'z', 'з': 'z', 'и': 'i', 'ј': 'j', 'к': 'k', 'л': 'l',
    'љ': 'lj','м': 'm', 'н': 'n', 'њ': 'nj', 'о': 'o', 'п': 'p',
    'р': 'r', 'с': 's', 'т': 't', 'ћ': 'c', 'у': 'u', 'ф': 'f',
    'х': 'h', 'ц': 'c', 'ч': 'c', 'џ': 'dz', 'ш': 's', 'ђ': 'dj',
    'č': 'c', 'ć': 'c', 'ž': 'z', 'š': 's', 'đ': 'dj'
}

cyr_to_lat = {
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E',
    'Ж': 'Ž', 'З': 'Z', 'И': 'I', 'Ј': 'J', 'К': 'K', 'Л': 'L',
    'М': 'M', 'Н': 'N', 'Њ': 'NJ', 'О': 'O', 'П': 'P', 'Р': 'R',
    'С': 'S', 'Т': 'T', 'Ћ': 'Ć', 'У': 'U', 'Ф': 'F', 'Х': 'H',
    'Ц': 'C', 'Ч': 'Č', 'Џ': 'DŽ', 'Ш': 'Š', 'Ђ': 'Đ', 'Љ': 'LJ',
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e',
    'ж': 'ž', 'з': 'z', 'и': 'i', 'ј': 'j', 'к': 'k', 'л': 'l',
    'љ': 'lj','м': 'm', 'н': 'n', 'њ': 'nj', 'о': 'o', 'п': 'p',
    'р': 'r', 'с': 's', 'т': 't', 'ћ': 'ć', 'у': 'u', 'ф': 'f',
    'х': 'h', 'ц': 'c', 'ч': 'č', 'џ': 'dž', 'ш': 'š', 'ђ': 'đ'
}


def normalize_name(name: str):
    if type(name) == float and math.isnan(name):
        return name
    if type(name) == int:
        return str(name)
    name = name.replace(' ', '').replace('.', '').replace('-', '').lower()

    normalized = ''
    for c in name:
        if c in normalize_rules:
            normalized += normalize_rules[c]
        else:
            normalized += c
    return normalized


def normalize_name_latin(name: str):
    if type(name) == float and math.isnan(name):
        return name
    if type(name) == int:
        return str(name)
    name = name.replace(' ', '').replace('.', '').replace('-', '').lower()

    normalized = ''
    for c in name:
        if c in cyr_to_lat:
            normalized += cyr_to_lat[c]
        else:
            normalized += c
    return normalized


def cyr2lat(text):
    if type(text) == int:
        return str(text)
    out = ''
    for c in text:
        if c in cyr_to_lat:
            out += cyr_to_lat[c]
        else:
            out += c
    return out


def xml_escape(str_xml):
    if type(str_xml) == int:
        return str
    str_xml = str_xml.replace("&", "&amp;")
    str_xml = str_xml.replace("<", "&lt;")
    str_xml = str_xml.replace(">", "&gt;")
    str_xml = str_xml.replace("\"", "&quot;")
    str_xml = str_xml.replace("'", "&apos;")
    return str_xml


def load_mappings(data_path):
    street_mappings = {}
    with open(os.path.join(data_path, 'mapping', 'mapping.csv'), encoding='utf-8') as mapping_csv_file:
        reader = csv.DictReader(mapping_csv_file)
        for row in reader:
            street_mappings[row['rgz_name']] = row['name']
    return street_mappings


def geojson2js(js_path, variable_name):
    with open(js_path, 'r') as f:
        js_data = json.load(f)
    for f in js_data['features']:
        geom = f['geometry']
        if geom['type'] != 'Polygon':
            continue
        new_coord_list = []
        for p in geom['coordinates']:
            new_coords = []
            for x, y in p:
                new_coords.append([round(x, 4), round(y, 4)])
            new_coord_list.append(new_coords)
        geom['coordinates'] = new_coord_list
    js_file_content = json.dumps(js_data)
    js_file_content = f'var {variable_name} = {js_file_content}'
    with open(js_path, 'w') as f:
        f.write(js_file_content)


class CollectRelationWaysHandler(osmium.SimpleHandler):
    """
    Iterates for all building relations and collects associated ways
    """
    def __init__(self, tag_to_search):
        osmium.SimpleHandler.__init__(self)
        self.ways = {}
        self.tag_to_search = tag_to_search

    def relation(self, r):
        if r.tags.get(self.tag_to_search):
            only_outer_ways = [m for m in r.members if m.type == 'w' and m.role == 'outer']
            for m in only_outer_ways:
                self.ways[m.ref] = {'role': m.role}


class CollectWayNodesHandler(osmium.SimpleHandler):
    """
    Iterates for all ways with tags to search and all ways previously found in relations and:
    * collects their nodes
    * build ways cache
    """
    def __init__(self, ways, tag_to_search):
        osmium.SimpleHandler.__init__(self)
        self.tag_to_search = tag_to_search
        self.ways = ways
        self.nodes = []
        self.ways_cache = {}

    def way(self, w):
        if w.tags.get(self.tag_to_search):
            for n in w.nodes:
                self.nodes.append(n.ref)
        if w.id in self.ways:
            self.ways_cache[w.id] = [n.ref for n in w.nodes]
            self.nodes += [n.ref for n in w.nodes]


class BuildNodesCacheHandler(osmium.SimpleHandler):
    """
    For all collected nodes, find all lat/long for them (create cache for nodes)
    """
    def __init__(self, nodes):
        osmium.SimpleHandler.__init__(self)
        self.nodes = nodes
        self.nodes_cache = {}

    def node(self, n):
        if n.id in self.nodes:
            self.nodes_cache[n.id] = {
                'lat': n.location.lat,
                'lon': n.location.lon
            }


class CollectEntitiesHandler(osmium.SimpleHandler):
    """
    Collects all entities and their geometries
    """
    def __init__(self, nodes_cache, ways_cache, tag_to_search, collect_only_nodes=False, collect_tags=False):
        osmium.SimpleHandler.__init__(self)
        self.tag_to_search = tag_to_search
        self.collect_only_nodes = collect_only_nodes
        self.collect_tags = collect_tags
        self.nodes_cache = nodes_cache
        self.ways_cache = ways_cache
        self.entities = []

    def geometry_from_way(self, way_nodes):
        coords = []
        first_node, last_node = None, None
        for node in way_nodes:
            if node in self.nodes_cache:
                if not first_node:
                    first_node = node
                last_node = node
                coords.append((self.nodes_cache[node]['lon'], self.nodes_cache[node]['lat']))
            else:
                raise Exception(f"Node {node} not found in cache, something is wrong")
        if len(coords) == 0:
            return None
        if len(coords) == 1:
            return geometry.Point((coords[0][0], coords[0][1]))
        else:
            if first_node == last_node:
                return geometry.Polygon(coords)
            else:
                return geometry.LineString(coords)

    def geometry_from_relation(self, r):
        only_outer_ways = [m for m in r.members if m.type == 'w' and m.role == 'outer']
        polygons = []
        for way in only_outer_ways:
            if way.ref not in self.ways_cache:
                continue
            way_nodes = self.ways_cache[way.ref]
            way_geometry = self.geometry_from_way(way_nodes)
            if not way_geometry:
                continue
            polygons.append(way_geometry)
        if len(polygons) == 0:
            return None
        if len(polygons) == 1:
            return polygons[0]
        else:
            if all(p.geom_type == 'Polygon' for p in polygons):
                return geometry.MultiPolygon(polygons)
            elif all(p.geom_type == 'LineString' for p in polygons):
                return geometry.MultiLineString(polygons).convex_hull
            else:
                return geometry.GeometryCollection(polygons).convex_hull

    def node(self, n):
        if n.tags.get(self.tag_to_search):
            point = geometry.Point((n.location.lon, n.location.lat))
            self.entities.append({
                'osm_id': 'n' + str(n.id),
                'osm_country': n.tags.get('addr:country'),
                'osm_city': n.tags.get('addr:city'),
                'osm_postcode': n.tags.get('addr:postcode'),
                'osm_street': n.tags.get('addr:street'),
                'osm_housenumber': n.tags.get('addr:housenumber'),
                'ref:RS:kucni_broj': n.tags.get('ref:RS:kucni_broj'),
                'tags': '{}' if not self.collect_tags else {k: v for k, v in n.tags},
                'osm_geometry': point
            })

    def way(self, w):
        if self.collect_only_nodes:
            return
        if w.tags.get(self.tag_to_search):
            street = w.tags.get('addr:street')
            housenumber = w.tags.get('addr:housenumber')
            geom = self.geometry_from_way([n.ref for n in w.nodes])
            if not geom:
                print(f"Dropping way {w.id} ({street or ''} {housenumber}) as its geometry cannot be calculated")
                return
            self.entities.append({
                'osm_id': 'w' + str(w.id),
                'osm_country': w.tags.get('addr:country'),
                'osm_city': w.tags.get('addr:city'),
                'osm_postcode': w.tags.get('addr:postcode'),
                'osm_street': street,
                'osm_housenumber': housenumber,
                'ref:RS:kucni_broj': w.tags.get('ref:RS:kucni_broj'),
                'tags': '{}' if not self.collect_tags else {k: v for k, v in w.tags},
                'osm_geometry': geom
            })

    def relation(self, r):
        if self.collect_only_nodes:
            return
        if r.tags.get(self.tag_to_search):
            street = r.tags.get('addr:street')
            housenumber = r.tags.get('addr:housenumber')
            geom = self.geometry_from_relation(r)
            if not geom:
                print(f"Dropping relation {r.id} as its geometry cannot be calculated")
                return
            self.entities.append({
                'osm_id': 'r' + str(r.id),
                'osm_country': r.tags.get('addr:country'),
                'osm_city': r.tags.get('addr:city'),
                'osm_postcode': r.tags.get('addr:postcode'),
                'osm_street': street,
                'osm_housenumber': housenumber,
                'ref:RS:kucni_broj': r.tags.get('ref:RS:kucni_broj'),
                'tags': '{}' if not self.collect_tags else {k: v for k, v in r.tags},
                'osm_geometry': geom
            })
