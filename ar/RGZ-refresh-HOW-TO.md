## Kako uraditi RGZ refresh

Sa vremena na vreme, treba da uvučemo nove podatke iz RGZ-a. Postupak nije baš lagan, evo koraci ovde.

### Skidanje podataka sa RGZ sajta

Pokrene se skripta src/download_from_rgz.py i onda skine sve .zip fajlove u data/rgz/download.

Onda se pokrene src/prepare_rgz_data.py koji od tih .zip fajlova napravi .csv fajlove u data/rgz/csv i jedan veliki
fajl data/rgz/addresses.csv.

Ukoliko je sve u redu (nijedna opština nije propuštena i sl.), ovi fajlovi će biti jako slične veličine i sa par razlika
(bude par hiljada adresa na mesec dana razlike).

### Update podataka u OSM-u

Stari veliki fajl data/rgz/addresses.csv treba preimenovati u addresses-old.csv. Novi se preimenuje u addresses-new.csv.

Sada može da se pokrene skripta src/generate_rgz_diff.py.

Izmeniti konstantu RGZ_LAST_UPDATE na početku. Skripta ima 3 dela, pogledati main i ne izvršavati je slepo.

* `create_csv_files` - ova funkcija uzima addresses-old.csv i addresses-new.csv i na osnovu njih pravi
addresses-added.csv, addresses-changed.csv i addresses-removed.csv. To sad može da se prebaci u Excel i okaču na forum.
* `fix_deleted_to_added` - ova funkcija čita addresses-added.csv i addresses-removed.csv. Poredi obrisane i dodate adrese
i ako obrisana adresa ima istu ulicu i broj kao neka novododata, onda menja `ref:RS:kucni_broj`. Ako nema, onda menja
`ref:RS:kucni_broj` sa `removed:ref:RS:kucni_broj` i dodaje `note` tag kada je obrisana adresa.
* `fix_changed` - ova funkcija prolazi kroz sve promenjene adrese i ako je promenjena, menja
`addr:street` i `addr:housenumber` u OSM-u

### Generisanje tile servera

Tile server generiše korisnik mpele, ali treba mu izgenerisati novi .shp fajl. Otvori se QGIS, učita se
data/rgz/addresses.csv (Layer->Add layer->Add Delimited Text Layer). Stavi se WKT i autodetect i EPSG:4326.

Treba sad uraditi reproject u EPSG:3857.

Sad treba novi sloj snimiti kao .shp. Desni klik na sloj, pa Export->Save Features As. Odabrati "ESRI Shapefile" i
odštiklirati sve osim "rgz_ulica" i "rgz_kucni_broj". Zipuju se svi dobijeni fajlovi (treba da bude oko 50MB) i pošalje
mpeletu (okači se link na forum).