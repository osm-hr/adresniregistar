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

with open(OUTPUT, "w", newline="", encoding="utf-8") as csvfile:

    if (ADMIN_TYPE == "Jedinica lokalne samouprave"):
        admin_fieldnames = [
            "opstina_maticni_broj",
            "opstina_ime",
            "opstina_imel",
            "opstina_povrsina",
            "okrug_sifra",
            "geometry",
            "inspire_id"
        ]
    elif (ADMIN_TYPE == "Naselje"):
        admin_fieldnames = [
            "objectid",
            "naselje_maticni_broj",
            "naselje_ime",
            "naselje_imel",
            "naselje_povrsina",
            "opstina_maticni_broj",
            "opstina_ime",
            "opstina_imel",
            "wkt",
            "inspire_id",
            "opstina_inspire_id"
        ]

    writer = csv.DictWriter(
        csvfile,
        fieldnames=admin_fieldnames
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

        if ADMIN_TYPE == "Jedinica lokalne samouprave":
            if maticni_broj == "5835":
                ime = "Općina Privlaka"
            elif maticni_broj == "3140":
                ime = "Općina Otok"
            elif maticni_broj == "4324":
                ime = "Općina Sveta Nedelja"

        if parent_id == "5835":
            parent_name = "Općina Privlaka"
        elif parent_id == "3140":
            parent_name = "Općina Otok"
        elif parent_id == "4324":
            parent_name = "Općina Sveta Nedelja"

        if (ADMIN_TYPE == "Jedinica lokalne samouprave"):
            writer.writerow({
                "opstina_maticni_broj": maticni_broj,
                "opstina_ime": ime,
                "opstina_imel": ime,
                "opstina_povrsina": "0",
                "okrug_sifra": "0",
                "geometry": geometry_wkt,
                "inspire_id": inspire_id
            })
        elif (ADMIN_TYPE == "Naselje"):
            writer.writerow({
                "objectid": "0",
                "naselje_maticni_broj": maticni_broj,
                "naselje_ime": ime,
                "naselje_imel": ime,
                "naselje_povrsina": "0",
                "opstina_ime": parent_name,
                "opstina_imel": parent_name,
                "wkt": geometry_wkt,
                "opstina_inspire_id": parent_id,
                "inspire_id": inspire_id
            })

        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

print(f"Done. Output written to {OUTPUT}")