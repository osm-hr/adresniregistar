import csv
import argparse
from lxml import etree

# -------------------------
# Argument parsing
# -------------------------
parser = argparse.ArgumentParser(
    description="Extract AdministrativeUnit data by type"
)
parser.add_argument(
    "admin_type",
    help='Administrative type (e.g. "Naselje" or "Jedinica lokalne samouprave")'
)
parser.add_argument(
    "--input",
    default="AdministrativeUnit.gml",
    help="Input GML file"
)
parser.add_argument(
    "--output",
    default="naselje.csv",
    help="Output CSV file"
)

args = parser.parse_args()

ADMIN_TYPE = args.admin_type
INPUT = args.input
OUTPUT = args.output

# -------------------------
# Namespaces
# -------------------------
AU_NS = "http://inspire.ec.europa.eu/schemas/au/4.0"
GMD_NS = "http://www.isotc211.org/2005/gmd"
GN_NS = "http://inspire.ec.europa.eu/schemas/gn/4.0"
GML_NS = "http://www.opengis.net/gml/3.2"
XLINK_NS = "http://www.w3.org/1999/xlink"
BASE_NS = "http://inspire.ec.europa.eu/schemas/base/3.3"

# -------------------------
# Dynamic naming
# -------------------------
if ADMIN_TYPE== "Naselje":
    prefix = "naselje"
    geo_column = "wkt"
    parent_column = "opstina_imel"
elif ADMIN_TYPE == "Jedinica lokalne samouprave":
    prefix = "opstina"
    geo_column = "geometry"
    parent_column = "zupanija_imel"

with open(OUTPUT, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(
        csvfile,
        fieldnames=[
            f"{prefix}_maticni_broj",
            f"{prefix}_ime",
            f"{prefix}_imel",
            "inspire_id",
            "parent_id",
            parent_column,
            geo_column
        ]
    )
    writer.writeheader()

    for event, elem in etree.iterparse(
        INPUT,
        events=("end",),
        tag=f"{{{AU_NS}}}AdministrativeUnit",
        huge_tree=True
    ):

        # Find matching admin type
        matches = elem.findall(f".//{{{GMD_NS}}}LocalisedCharacterString")
        if not any(ADMIN_TYPE in (m.text or "") for m in matches):
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
            continue

        # nationalCode
        code_elem = elem.find(f"./{{{AU_NS}}}nationalCode")
        if code_elem is not None and code_elem.text:
            maticni_broj = code_elem.text.strip().lstrip("0")
            if maticni_broj == "":   # handles case like "0000"
                maticni_broj = "0"
        else:
            maticni_broj = ""

        # inspireId
        if ADMIN_TYPE == "Naselje":
            inspire_id_elem = elem.find(
                f"./{{{AU_NS}}}inspireId/{{{BASE_NS}}}Identifier/{{{BASE_NS}}}localId"
            )
            inspire_id = inspire_id_elem.text.strip() if inspire_id_elem is not None else ""
        elif ADMIN_TYPE == "Jedinica lokalne samouprave":
            inspire_id = elem.attrib.get(f"{{{GML_NS}}}id", "").strip()

        # name
        name_elem = elem.find(f".//{{{GN_NS}}}text")
        ime = name_elem.text.strip() if name_elem is not None else ""

        # Parent
        parent_id = ""
        parent_name = ""

        upper = elem.find(f"./{{{AU_NS}}}upperLevelUnit")
        if upper is not None:
            href = upper.get(f"{{{XLINK_NS}}}href")
            title = upper.get(f"{{{XLINK_NS}}}title")

            if href:
                parent_id = href.replace("#", "")
            if title:
                parent_name = title.strip()

        # Geometry
        polygons = []

        for polygon in elem.findall(f".//{{{GML_NS}}}Polygon"):
            exterior = polygon.find(
                f".//{{{GML_NS}}}exterior/{{{GML_NS}}}LinearRing/{{{GML_NS}}}posList"
            )
            if exterior is None:
                continue

            coords = exterior.text.strip().split()
            points = []

            for i in range(0, len(coords), 2):
                x = coords[i]
                y = coords[i + 1]
                points.append(f"{y} {x}")

            polygons.append(f"(({','.join(points)}))")

        if len(polygons) == 1:
            geometry_wkt = f"POLYGON{polygons[0]}"
        elif len(polygons) > 1:
            geometry_wkt = f"MULTIPOLYGON({','.join(polygons)})"
        else:
            geometry_wkt = ""

        writer.writerow({
            f"{prefix}_maticni_broj": maticni_broj,
            f"{prefix}_ime": ime,
            f"{prefix}_imel": ime,
            "inspire_id": inspire_id,
            "parent_id": parent_id,
            parent_column: parent_name,
            geo_column: geometry_wkt
        })

        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

print(f"Done. Output written to {OUTPUT}")