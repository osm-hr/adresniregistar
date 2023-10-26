import csv
import functools
import http
import os
import socket
import time
import urllib

import overpy
from overpy.exception import OverpassTooManyRequests, OverpassGatewayTimeout, OverpassUnknownContentType
from shapely import geometry
from shapely.ops import linemerge, unary_union, polygonize


def retry_on_error(timeout_in_seconds=60):
    def decorate(func):
        def call(*args, **kwargs):
            retries = 5
            while retries > 0:
                try:
                    result = func(*args, **kwargs)
                except (ConnectionRefusedError, ConnectionResetError,
                        OverpassTooManyRequests, OverpassGatewayTimeout, OverpassUnknownContentType,
                        socket.timeout, urllib.error.URLError, http.client.RemoteDisconnected):
                    retries = retries - 1
                    print('Connection refused, retrying')
                    time.sleep(timeout_in_seconds)
                    continue
                return result
            raise Exception('Exhausted retries for connection refused, quitting')
        return call
    return decorate


def create_geometry_from_osm_response(relation, response):
    # Try to build shapely polygon out of this data
    outer_ways = [way.ref for way in relation.members if way.role == 'outer']
    inner_ways = [way.ref for way in relation.members if way.role == 'inner']
    lss = []
    for ii_w, way in enumerate(response.ways):
        if way.id not in outer_ways:
            continue
        ls_coords = []
        for node in way.nodes:
            ls_coords.append((node.lon, node.lat))
        lss.append(geometry.LineString(ls_coords))

    merged = linemerge([*lss])
    borders = unary_union(merged)
    polygons = list(polygonize(borders))
    polygon = functools.reduce(lambda p,x: p.union(x), polygons[1:], polygons[0])
    if len(inner_ways) > 0:
        lss_inner = []
        for ii_w, way in enumerate(response.ways):
            if way.id not in inner_ways:
                continue
            ls_coords = []
            for node in way.nodes:
                ls_coords.append((node.lon, node.lat))
            lss_inner.append(geometry.LineString(ls_coords))
        merged = linemerge([*lss_inner])
        borders = unary_union(merged)
        inner_polygons = list(polygonize(borders))
        for inner_polygon in inner_polygons:
            polygon = polygon.symmetric_difference(inner_polygon)
    return polygon


@retry_on_error(timeout_in_seconds=2*60)
def get_entities(overpass_api, from_lat, from_lon, to_lat, to_lon):
    entities = []
    response = overpass_api.query(f"""
        [bbox:{from_lat},{from_lon},{to_lat},{to_lon}]
        [out:json];
        area["name"="Србија"]["admin_level"=2]->.c;
        (
            node(area.c)["addr:housenumber"];
            way(area.c)["addr:housenumber"];
            relation(area.c)["addr:housenumber"];
        );
        (._;>;);
        out;
        // &contact=https://gitlab.com/osm-serbia/adresniregistar
    """)
    for n in response.nodes:
        if not n.tags.get('addr:housenumber'):
            continue
        geom = geometry.Point((n.lon, n.lat))
        entities.append({
            'osm_id': 'n' + str(n.id),
            'osm_country': n.tags.get('addr:country'),
            'osm_city': n.tags.get('addr:city'),
            'osm_postcode': n.tags.get('addr:postcode'),
            'osm_street': n.tags.get('addr:street'),
            'osm_housenumber': n.tags.get('addr:housenumber'),
            'ref:RS:kucni_broj': n.tags.get('ref:RS:kucni_broj'),
            'tags': '{}',
            'note': n.tags.get('note') if 'note' in n.tags else '',
            'osm_geometry': geom,
        })
    for w in response.ways:
        if not w.tags.get('addr:housenumber'):
            continue
        ls_coords = []
        for node in w.nodes:
            ls_coords.append((node.lon, node.lat))
        if len(w.nodes) == 1:
            geom = geometry.Point((w.nodes[0].lon, w.nodes[0].lat))
        elif w.nodes[0].id != w.nodes[-1].id:
            geom = geometry.LineString(ls_coords)
        else:
            geom = geometry.Polygon(ls_coords)
        entities.append({
            'osm_id': 'w' + str(w.id),
            'osm_country': w.tags.get('addr:country'),
            'osm_city': w.tags.get('addr:city'),
            'osm_postcode': w.tags.get('addr:postcode'),
            'osm_street': w.tags.get('addr:street'),
            'osm_housenumber': w.tags.get('addr:housenumber'),
            'ref:RS:kucni_broj': w.tags.get('ref:RS:kucni_broj'),
            'tags': '{}',
            'note': w.tags.get('note') if 'note' in w.tags else '',
            'osm_geometry': geom
        })
    for r in response.relations:
        if not r.tags.get('addr:housenumber'):
            continue
        geom = create_geometry_from_osm_response(r, response)
        entities.append({
            'osm_id': 'r' + str(r.id),
            'osm_country': r.tags.get('addr:country'),
            'osm_city': r.tags.get('addr:city'),
            'osm_postcode': r.tags.get('addr:postcode'),
            'osm_street': r.tags.get('addr:street'),
            'osm_housenumber': r.tags.get('addr:housenumber'),
            'ref:RS:kucni_broj': r.tags.get('ref:RS:kucni_broj'),
            'tags': '{}',
            'note': r.tags.get('note') if 'note' in r.tags else '',
            'osm_geometry': geom
        })
    return entities


def main():
    cwd = os.getcwd()
    collect_path = os.path.join(cwd, 'data/osm')
    all_addresses_path = os.path.join(collect_path, 'addresses.csv')

    if os.path.exists(all_addresses_path) and os.path.getsize(all_addresses_path) > 1024 * 1024:
        print("Skipping creation of data/osm/addresses.csv as it already exists")
        return

    # overpass_api = overpy.Overpass(url='http://overpass-api.de/api/interpreter')
    # overpass_api = overpy.Overpass(url='https://lz4.overpass-api.de/api/interpreter')
    overpass_api = overpy.Overpass(url='http://localhost:12346/api/interpreter')

    all_entities = []
    all_entities_ids = set()

    lats = [lat/10 for lat in range(420, 465, 5)]
    lons = [lon / 10 for lon in range(185, 230, 5)]
    i = 1
    for from_lat in lats:
        for from_lon in lons:
            entities_in_bbox = get_entities(overpass_api, from_lat, from_lon, from_lat + 0.5, from_lon + 0.5)
            for entity_in_bbox in entities_in_bbox:
                if entity_in_bbox['osm_id'] in all_entities_ids:
                    continue
                all_entities.append(entity_in_bbox)

            print(f"Collected {len(all_entities)} up to now ({i}/{len(lats) * len(lons)})")

            if 'localhost' not in overpass_api.url:
                time.sleep(5)
            i = i + 1

    print(f"Found {len(all_entities)} entities")
    with open(all_addresses_path, 'w', encoding="utf-8") as all_addresses_csv:
        writer = csv.DictWriter(
            all_addresses_csv,
            fieldnames=['osm_id', 'osm_country', 'osm_city', 'osm_postcode', 'osm_street', 'osm_housenumber', 'ref:RS:ulica', 'ref:RS:kucni_broj', 'tags', 'note', 'osm_geometry'])
        writer.writeheader()
        for address in all_entities:
            writer.writerow(address)
    print(f"All {len(all_entities)} addresses written to data/osm/addresses.csv")


if __name__ == '__main__':
    main()
