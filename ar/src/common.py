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

cyr_to_norm = {
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E',
    'Ж': 'Z', 'З': 'Z', 'И': 'I', 'Ј': 'J', 'К': 'K', 'Л': 'L',
    'М': 'M', 'Н': 'N', 'Њ': 'Nj', 'О': 'O', 'П': 'P', 'Р': 'R',
    'С': 'S', 'Т': 'T', 'Ћ': 'C', 'У': 'U', 'Ф': 'F', 'Х': 'H',
    'Ц': 'C', 'Ч': 'C', 'Џ': 'Dz', 'Ш': 'S', 'Ђ': 'Dj', 'Љ': 'Lj',
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e',
    'ж': 'z', 'з': 'z', 'и': 'i', 'ј': 'j', 'к': 'k', 'л': 'l',
    'љ': 'lj','м': 'm', 'н': 'n', 'њ': 'nj', 'о': 'o', 'п': 'p',
    'р': 'r', 'с': 's', 'т': 't', 'ћ': 'c', 'у': 'u', 'ф': 'f',
    'х': 'h', 'ц': 'c', 'ч': 'c', 'џ': 'dz', 'ш': 's', 'ђ': 'dj'
}


cyr_to_lat_small = {
    'Њ': 'Nj', 'Џ': 'Dž', 'Љ': 'Lj'
}

housenumber_order = {
    'a': 1, 'b': 2, 'v': 3, 'g': 4, 'd': 5, 'đ': 6, 'e': 7, 'ž': 8, 'z': 9, 'i': 10,
    'j': 11, 'k': 12, 'l': 13, 'lj': 14, 'm': 15, 'n': 16, 'nj': 17, 'o': 18, 'p': 19, 'r': 20,
    's': 21, 't': 22, 'ć': 23, 'u': 24, 'f': 25, 'h': 26, 'c': 27, 'č': 28, 'dž': 29, 'š': 30,
}


class ApartmentResolution(Enum):
    OSM_ENTITY_NOT_FOUND = 1  # recently deleted or recently added
    NODE_DETACHED = 2  # node is detached, cannot be building=apartments
    OSM_ENTITY_NOT_BUILDING = 3  # If entity is node, it is attached to something that is not tagged as building. If it is way or relation, it is not tagged as building
    OSM_ENTITY_NOT_APARTMENT = 4  # If entity is node, it is attached to something that is not tagged as building=apartments. If it is way or relation, it is not tagged as building=apartments
    OSM_ENTITY_APARTMENT = 5  # All is OK


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


def cyr2lat_small(text):
    if type(text) == int:
        return str(text)
    out = ''
    for c in text:
        if c in cyr_to_lat_small:
            out += cyr_to_lat_small[c]
        elif c in cyr_to_lat:
            out += cyr_to_lat[c]
        else:
            out += c
    return out


def cyr2intname(text):
    if type(text) == int:
        return str(text)
    out = ''
    for c in text:
        if c in cyr_to_norm:
            out += cyr_to_norm[c]
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
    with open(js_path, 'r', encoding='utf-8') as f:
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


def pad_housenumber(housenumber):
    if type(housenumber) != str:
        return '00000'
    if len(housenumber) == 0:
        return '00000'

    if housenumber[-1].isdigit():
        return f'{housenumber:>05}'

    if len(housenumber) > 1:
        if housenumber[-2].isdigit():
            # Case of only one letter, "12a"
            number = housenumber[0:-1]
            letter = housenumber[-1]
            return f'{number:>05}{letter}'
        else:
            # Case with two letters, "12lj"
            number = housenumber[0:-2]
            letter = housenumber[-2:]
            return f'{number:>05}{letter}'
    else:
        if housenumber[0].isdigit():
            # Case with one char, "1"
            return f'{housenumber:>05}'
        else:
            # Case with one char, letter, "a"
            return f'{housenumber:>05}'


def housenumber_to_float(housenumber):
    if type(housenumber) != str:
        return 0

    if len(housenumber) == 0:
        return 0

    if housenumber[-1].isdigit():
        return int(housenumber)

    if len(housenumber) > 1:
        if housenumber[-2].isdigit():
            # Case of only one letter, "12a"
            number = int(housenumber[0:-1])
            letter = housenumber[-1]
        else:
            # Case with two letters, "12lj"
            number = housenumber[0:-2]
            letter = housenumber[-2:]
    else:
        if housenumber[0].isdigit():
            # Case with one char, "1"
            return int(housenumber)
        else:
            # Case with one char, letter, "a"
            number = 0
            letter = housenumber[0]
    if letter in housenumber_order:
        return round(number + housenumber_order[letter]/30, 3)
    else:
        return number


class CollectRelationWaysHandler(osmium.SimpleHandler):
    """
    Iterates for all building relations and collects associated ways
    """
    def __init__(self, tags_to_search):
        osmium.SimpleHandler.__init__(self)
        self.ways = {}
        if type(tags_to_search) == str:
            self.tags_to_search = set([tags_to_search])
        else:
            self.tags_to_search = set(tags_to_search)

    def relation(self, r):
        for tag_to_search in self.tags_to_search:
            if r.tags.get(tag_to_search):
                outer_inner_ways = [m for m in r.members if m.type == 'w' and m.role == 'outer' or m.role == 'inner']
                for m in outer_inner_ways:
                    self.ways[m.ref] = {'role': m.role}
                break


class CollectWayNodesHandler(osmium.SimpleHandler):
    """
    Iterates for all ways with tags to search and all ways previously found in relations and:
    * collects their nodes
    * build ways cache
    """
    def __init__(self, ways, tags_to_search):
        osmium.SimpleHandler.__init__(self)
        if type(tags_to_search) == str:
            self.tags_to_search = set([tags_to_search])
        else:
            self.tags_to_search = set(tags_to_search)
        self.ways = ways
        self.nodes = []
        self.ways_cache = {}

    def way(self, w):
        for tag_to_search in self.tags_to_search:
            if w.tags.get(tag_to_search):
                for n in w.nodes:
                    self.nodes.append(n.ref)
                break
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
    def __init__(self, nodes_cache, ways_cache, tags_to_search, collect_only_nodes=False, collect_tags=False):
        osmium.SimpleHandler.__init__(self)
        if type(tags_to_search) == str:
            self.tags_to_search = set([tags_to_search])
        else:
            self.tags_to_search = set(tags_to_search)
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
            if first_node == last_node and len(coords) > 2:
                return geometry.Polygon(coords)
            else:
                return geometry.LineString(coords)

    def geometry_from_relation(self, r):
        only_outer_ways = [m for m in r.members if m.type == 'w' and m.role == 'outer']
        only_inner_ways = [m for m in r.members if m.type == 'w' and m.role == 'inner']
        outer_polygons, inner_polygons = [], []
        for way in only_outer_ways:
            if way.ref not in self.ways_cache:
                continue
            way_nodes = self.ways_cache[way.ref]
            way_geometry = self.geometry_from_way(way_nodes)
            if not way_geometry:
                continue
            outer_polygons.append(way_geometry)
        if len(outer_polygons) == 0:
            return None

        if all(p.geom_type == 'LineString' for p in outer_polygons):
            return geometry.MultiLineString(outer_polygons).convex_hull

        for way in only_inner_ways:
            if way.ref not in self.ways_cache:
                continue
            way_nodes = self.ways_cache[way.ref]
            way_geometry = self.geometry_from_way(way_nodes)
            if not way_geometry:
                continue
            inner_polygons.append(way_geometry)
        all_inner_polygons = None
        if len(inner_polygons) == 1:
            all_inner_polygons = inner_polygons[0]
        elif all(p.geom_type == 'Polygon' for p in inner_polygons):
            all_inner_polygons = geometry.MultiPolygon(inner_polygons)
        else:
            all_inner_polygons = geometry.GeometryCollection(inner_polygons)

        if len(outer_polygons) == 1:
            all_outer_polygons = outer_polygons[0]
        if all(p.geom_type == 'Polygon' for p in outer_polygons):
            all_outer_polygons = geometry.MultiPolygon(outer_polygons)
        else:
            all_outer_polygons = geometry.GeometryCollection(outer_polygons)

        if not all_inner_polygons:
            return all_outer_polygons
        else:
            return all_outer_polygons.difference(all_inner_polygons)

    def node(self, n):
        for tag_to_search in self.tags_to_search:
            if n.tags.get(tag_to_search):
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
                    'note': n.tags.get('note') if 'note' in n.tags else '',
                    'osm_geometry': point
                })
                break

    def way(self, w):
        if self.collect_only_nodes:
            return
        for tag_to_search in self.tags_to_search:
            if w.tags.get(tag_to_search):
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
                    'note': w.tags.get('note') if 'note' in w.tags else '',
                    'osm_geometry': geom
                })
                break

    def relation(self, r):
        if self.collect_only_nodes:
            return
        for tag_to_search in self.tags_to_search:
            if r.tags.get(tag_to_search):
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
                    'note': r.tags.get('note') if 'note' in r.tags else '',
                    'osm_geometry': geom
                })
                break


class OsmEntitiesCacheHandler(osmium.SimpleHandler):
    def __init__(self, nodes, ways):
        osmium.SimpleHandler.__init__(self)
        self.nodes = nodes
        self.ways = ways
        self.nodes_cache = {}
        self.ways_cache = {}

    def node(self, n):
        if n.id in self.nodes:
            self.nodes_cache[n.id] = {
                'lat': n.location.lat,
                'lon': n.location.lon,
                'tags': {t.k: t.v for t in n.tags},
                'version': n.version
            }

    def way(self, w):
        if w.id in self.ways:
            self.ways_cache[w.id] = {
                'tags': {t.k: t.v for t in w.tags},
                'nodes': [n.ref for n in w.nodes],
                'version': w.version
            }
