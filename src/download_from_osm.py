# -*- coding: utf-8 -*-

import csv
import os
import sys

import osmium
from shapely import geometry

csv.field_size_limit(sys.maxsize)


class CollectRelationWaysHandler(osmium.SimpleHandler):
    """
    Iterates for all relations with addresses and collects associated ways
    """
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.ways = {}

    def relation(self, r):
        if r.tags.get('addr:housenumber'):
            only_outer_ways = [m for m in r.members if m.type == 'w' and m.role == 'outer']
            for m in only_outer_ways:
                self.ways[m.ref] = {'role': m.role}


class CollectWayNodesHandler(osmium.SimpleHandler):
    """
    Iterates for all ways with addresses and all ways previously found in relations and:
    * collects their nodes
    * build ways cache
    """
    def __init__(self, ways):
        osmium.SimpleHandler.__init__(self)
        self.ways = ways
        self.nodes = []
        self.ways_cache = {}

    def way(self, w):
        if w.tags.get('addr:housenumber'):
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


class CollectAddressesHandler(osmium.SimpleHandler):
    """
    Collects all addresses and their geometries
    """
    def __init__(self, nodes_cache, ways_cache):
        osmium.SimpleHandler.__init__(self)
        self.nodes_cache = nodes_cache
        self.ways_cache = ways_cache
        self.addresses = []

    def geometry_from_way(self, way_nodes):
        coords = []
        first_node, last_node = None, None
        for node in way_nodes:
            if node in self.nodes_cache:
                if not first_node:
                    first_node = node
                last_node = node
                coords.append((self.nodes_cache[node]['lon'], self.nodes_cache[node]['lat']))
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
            if all(p.type == 'Polygon' for p in polygons):
                return geometry.MultiPolygon(polygons)
            elif all(p.type == 'LineString' for p in polygons):
                return geometry.MultiLineString(polygons).convex_hull
            else:
                return geometry.GeometryCollection(polygons).convex_hull

    def node(self, n):
        if n.tags.get('addr:housenumber'):
            point = geometry.Point((n.location.lon, n.location.lat))
            self.addresses.append({
                'id': 'n' + str(n.id),
                'country': n.tags.get('addr:country') or '',
                'city': n.tags.get('addr:city') or '',
                'postcode': n.tags.get('addr:postcode') or '',
                'street': n.tags.get('addr:street') or '',
                'housenumber': n.tags.get('addr:housenumber'),
                'geometry': point,
                'centroid': point
            })

    def way(self, w):
        if w.tags.get('addr:housenumber'):
            street = w.tags.get('addr:street') or ''
            housenumber = w.tags.get('addr:housenumber')
            geom = self.geometry_from_way([n.ref for n in w.nodes])
            if not geom:
                print(f"Dropping way {w.id} ({street} {housenumber}) as its geometry cannot be calculated")
                return
            self.addresses.append({
                'id': 'w' + str(w.id),
                'country': w.tags.get('addr:country') or '',
                'city': w.tags.get('addr:city') or '',
                'postcode': w.tags.get('addr:postcode') or '',
                'street': street,
                'housenumber': housenumber,
                'geometry': geom,
                'centroid': geom.centroid
            })

    def relation(self, r):
        if r.tags.get('addr:housenumber'):
            street = r.tags.get('addr:street') or ''
            housenumber = r.tags.get('addr:housenumber')
            geom = self.geometry_from_relation(r)
            if not geom:
                print(f"Dropping relation {r.id} ({street} {housenumber}) as its geometry cannot be calculated")
                return
            self.addresses.append({
                'id': 'r' + str(r.id),
                'country': r.tags.get('addr:country') or '',
                'city': r.tags.get('addr:city') or '',
                'postcode': r.tags.get('addr:postcode') or '',
                'street': street,
                'housenumber': housenumber,
                'geometry': geom,
                'centroid': geom.centroid
            })


def main():
    cwd = os.getcwd()
    collect_path = os.path.join(cwd, 'data/osm')
    pbf_file = os.path.join(collect_path, 'download/serbia.osm.pbf')

    crwh = CollectRelationWaysHandler()
    crwh.apply_file(pbf_file)
    print(f"Collected all ways ({len(crwh.ways)}) from relations")

    cwnh = CollectWayNodesHandler(crwh.ways)
    cwnh.apply_file(pbf_file)
    print(f"Collected all nodes ({len(cwnh.nodes)}) from ways")

    bnch = BuildNodesCacheHandler(set(cwnh.nodes))
    bnch.apply_file(pbf_file)
    print(f"Found coordinates for all nodes ({len(bnch.nodes_cache)})")

    cah = CollectAddressesHandler(bnch.nodes_cache, cwnh.ways_cache)
    cah.apply_file(pbf_file)
    print(f"Collected all addresses ({len(cah.addresses)})")

    all_addresses_path = os.path.join(collect_path, 'osm_addresses.csv')
    with open(all_addresses_path, 'w') as all_addresses_csv:
        writer = csv.DictWriter(
            all_addresses_csv,
            fieldnames=['id', 'country', 'city', 'postcode', 'street', 'housenumber', 'geometry', 'centroid'])
        writer.writeheader()
        for address in cah.addresses:
            writer.writerow(address)
    print(f"All {len(cah.addresses)} addresses written to osm_addresses.csv")


if __name__ == '__main__':
    main()
