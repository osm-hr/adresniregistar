import csv
from lxml import etree

INPUT = "data/rgz/unzip/AdministrativeUnit.gml"
OUTPUT = "data/rgz/opstina.csv"

AU_NS = "http://inspire.ec.europa.eu/schemas/au/4.0"
GMD_NS = "http://www.isotc211.org/2005/gmd"
GN_NS = "http://inspire.ec.europa.eu/schemas/gn/4.0"
GML_NS = "http://www.opengis.net/gml/3.2"

with open(OUTPUT, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=["opstina_maticni_broj", "opstina_ime", "geometry"])
    writer.writeheader()

    for event, elem in etree.iterparse(INPUT, events=("end",), tag=f"{{{AU_NS}}}AdministrativeUnit", huge_tree=True):

        # Check if this is a JLS
        lcs = elem.find(f".//{{{GMD_NS}}}LocalisedCharacterString")
        if lcs is None or "Jedinica lokalne samouprave" not in (lcs.text or ""):
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
            continue

        # Extract nationalCode
        code_elem = elem.find(f"./{{{AU_NS}}}nationalCode")
        opstina_maticni_broj = code_elem.text.strip() if code_elem is not None else ""

        # Extract municipality name
        name_elem = elem.find(f".//{{{GN_NS}}}text")
        opstina_ime = name_elem.text.strip() if name_elem is not None else ""

        # Extract geometry
        polys = []
        for poslist in elem.findall(f".//{{{GML_NS}}}posList"):
            coords = poslist.text.strip().split()
            # GML posList is space-separated: x1 y1 x2 y2 ...
            points = []
            for i in range(0, len(coords), 2):
                x, y = coords[i], coords[i+1]
                points.append(f"{x} {y}")
            # wrap as POLYGON (one outer ring)
            polys.append(f"({','.join(points)})")

        if len(polys) == 1:
            geometry_wkt = f"POLYGON{polys[0]}"
        else:
            geometry_wkt = f"MULTIPOLYGON({','.join(polys)})"

        # Write to CSV
        writer.writerow({
            "opstina_maticni_broj": opstina_maticni_broj,
            "opstina_ime": opstina_ime,
            "geometry": geometry_wkt
        })

        # free memory
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]
