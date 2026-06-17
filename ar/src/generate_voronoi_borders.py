from collections import defaultdict

from shapely.geometry import MultiPoint, Point, Polygon
from shapely.ops import voronoi_diagram


def generate_voronoi_borders(boundary: Polygon, points_with_ids: list[tuple[float, float, object]]) -> dict:
    """
    Tiles a boundary polygon into Voronoi regions, one per group.

    boundary: shapely Polygon (e.g. municipality or country border)
    points_with_ids: list of (x, y, group_id) — one representative point per group

    Returns: dict of group_id -> shapely Polygon clipped to boundary
    """
    if not points_with_ids:
        return {}

    if len(points_with_ids) == 1:
        _, _, gid = points_with_ids[0]
        return {gid: boundary}

    coords = [(x, y) for x, y, _ in points_with_ids]
    group_ids = [gid for _, _, gid in points_with_ids]

    regions = voronoi_diagram(MultiPoint(coords), envelope=boundary)

    # Each Voronoi region contains exactly its seed point — find it via min distance
    # (coords list is small: one centroid per settlement, typically < 100 per municipality)
    group_polygons = {}
    for region in regions.geoms:
        centroid = region.centroid
        idx = min(range(len(coords)), key=lambda i: centroid.distance(Point(coords[i])))
        clipped = region.intersection(boundary)
        if not clipped.is_empty:
            group_polygons[group_ids[idx]] = clipped

    return group_polygons


if __name__ == '__main__':
    import csv
    import sys
    from shapely import wkt as swkt

    csv.field_size_limit(sys.maxsize)

    addresses_path = 'data/rgz/addresses.csv'
    opstine_path = 'data/rgz/opstina.csv'
    output_path = 'data/rgz/naselje.csv'

    print("Reading opstina.csv...")
    opstine = {}
    with open(opstine_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            opstine[row['opstina_maticni_broj']] = row

    print("Reading addresses.csv...")
    # Accumulate address points grouped by municipality → settlement
    by_opstina: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    settlement_names: dict[str, str] = {}

    with open(addresses_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            mb = row['rgz_opstina_mb']
            inspire_id = row['rgz_naselje_inspire_id']
            if not inspire_id:
                continue
            pt = swkt.loads(row['rgz_geometry'])
            by_opstina[mb][inspire_id].append((pt.x, pt.y))
            settlement_names[inspire_id] = row['rgz_naselje']

    total = len(opstine)
    print(f"Generating Voronoi for {total} municipalities...")
    rows = []
    for i, (mb, opstina) in enumerate(opstine.items(), 1):
        settlements = by_opstina.get(mb)
        if not settlements:
            continue

        # One centroid per settlement — keeps Voronoi seed count tiny (~5–50 per municipality)
        points_with_ids = []
        for inspire_id, pts in settlements.items():
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            points_with_ids.append((cx, cy, inspire_id))

        boundary = swkt.loads(opstina['geometry'])
        voronoi_regions = generate_voronoi_borders(boundary, points_with_ids)

        for inspire_id, polygon in voronoi_regions.items():
            rows.append({
                'object_id': inspire_id,
                'naselje_maticni_broj': inspire_id,
                'naselje_ime': settlement_names.get(inspire_id, ''),
                'naselje_imel': settlement_names.get(inspire_id, ''),
                'naselje_povrsina': '0',
                'opstina_maticni_broj': opstina['opstina_maticni_broj'],
                'opstina_ime': opstina['opstina_imel'],
                'opstina_imel': opstina['opstina_imel'],
                'wkt': polygon.wkt,
            })

        if i % 50 == 0:
            print(f"  {i}/{total} municipalities processed, {len(rows)} settlements so far")

    print(f"Writing {len(rows)} settlements to {output_path}...")
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'object_id', 'naselje_maticni_broj', 'naselje_ime', 'naselje_imel',
            'naselje_povrsina', 'opstina_maticni_broj', 'opstina_ime', 'opstina_imel', 'wkt',
        ])
        writer.writeheader()
        writer.writerows(rows)

    print("Done.")
