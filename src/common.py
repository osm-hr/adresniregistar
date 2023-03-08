# -*- coding: utf-8 -*-

import math

import osmium
from shapely import geometry

OPSTINE_TO_SKIP = ['VITINA', 'VUČITRN', 'GLOGOVAC', 'GNJILANE', 'GORA', 'DEČANI', 'ĐAKOVICA',
                   'ZVEČAN', 'ZUBIN POTOK', 'ISTOK', 'KAČANIK', 'KLINA', 'KOSOVSKA MITROVICA',
                   'KOSOVO POLJE', 'KOSOVSKA KAMENICA', 'LEPOSAVIĆ', 'LIPLJAN', 'NOVO BRDO',
                   'OBILIĆ', 'ORAHOVAC', 'PEĆ', 'PODUJEVO', 'PRIŠTINA', 'PRIZREN', 'SRBICA',
                   'SUVA REKA', 'UROŠEVAC', 'ŠTIMLJE', 'ŠTRPCE']

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
    out = ''
    for c in text:
        if c in cyr_to_lat:
            out += cyr_to_lat[c]
        else:
            out += c
    return out


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
    def __init__(self, nodes_cache, ways_cache, tag_to_search, collect_only_nodes=False):
        osmium.SimpleHandler.__init__(self)
        self.tag_to_search = tag_to_search
        self.collect_only_nodes = collect_only_nodes
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
                'osm_country': n.tags.get('addr:country') or '',
                'osm_city': n.tags.get('addr:city') or '',
                'osm_postcode': n.tags.get('addr:postcode') or '',
                'osm_street': n.tags.get('addr:street') or '',
                'osm_housenumber': n.tags.get('addr:housenumber'),
                'ref:RS:ulica': n.tags.get('ref:RS:ulica'),
                'ref:RS:kucni_broj': n.tags.get('ref:RS:kucni_broj'),
                'osm_geometry': point
            })

    def way(self, w):
        if self.collect_only_nodes:
            return
        if w.tags.get(self.tag_to_search):
            street = w.tags.get('addr:street') or ''
            housenumber = w.tags.get('addr:housenumber')
            geom = self.geometry_from_way([n.ref for n in w.nodes])
            if not geom:
                print(f"Dropping way {w.id} ({street} {housenumber}) as its geometry cannot be calculated")
                return
            self.entities.append({
                'osm_id': 'w' + str(w.id),
                'osm_country': w.tags.get('addr:country') or '',
                'osm_city': w.tags.get('addr:city') or '',
                'osm_postcode': w.tags.get('addr:postcode') or '',
                'osm_street': street,
                'osm_housenumber': housenumber,
                'ref:RS:ulica': w.tags.get('ref:RS:ulica'),
                'ref:RS:kucni_broj': w.tags.get('ref:RS:kucni_broj'),
                'osm_geometry': geom
            })

    def relation(self, r):
        if self.collect_only_nodes:
            return
        if r.tags.get(self.tag_to_search):
            street = r.tags.get('addr:street') or ''
            housenumber = r.tags.get('addr:housenumber')
            geom = self.geometry_from_relation(r)
            if not geom:
                print(f"Dropping relation {r.id} as its geometry cannot be calculated")
                return
            self.entities.append({
                'osm_id': 'r' + str(r.id),
                'osm_country': r.tags.get('addr:country') or '',
                'osm_city': r.tags.get('addr:city') or '',
                'osm_postcode': r.tags.get('addr:postcode') or '',
                'osm_street': street,
                'osm_housenumber': housenumber,
                'ref:RS:ulica': r.tags.get('ref:RS:ulica'),
                'ref:RS:kucni_broj': r.tags.get('ref:RS:kucni_broj'),
                'osm_geometry': geom
            })
