# Ulice iz adresnog registra

## Instalacija

Pokrenuti `python3 -m pip install -r requirements.txt` za instalaciju svih zavisnosti.

Pored toga u direktorijum `data/rgz` treba skinuti sa opendata.geosrbija.rs opstina.csv i naselje.csv.

Treba skinuti i [`geckodriver` binary](https://github.com/mozilla/geckodriver/releases) i staviti ga u root projekta.

ST modul zavisi da u AR modulu postoji `data/mapping/mapping.csv` fajl koji se generiše u AR modulu.

Treba da imate i `parallel` program (na Debian-u se prosto instalira sa `sudo apt install parallel`).

## Korišćenje

Sve komande se izvršavaju sa `make <komanda>`.

* Pokrenuti `make clean_osm` da očistite sve generisane podatke osim RGZ podataka
* Pokrenuti `make clean` za čišćenje svih podataka (PAŽNJA: obrisaće i RGZ podatke koji se teško skidaju)
* Za skidanje RGZ ulica koristiti `make download_from_rgz`. Za ovo treba headless browser (ja sam stavio `geckodriver` u root dir ST modula i to radi)
* Za generisanje izveštaja koristiti `make report` i izlaz treba da bude HTML izveštaj u data/report direktorijumu

## Osvežavanje sa RGZ-a

Osvežavanje nije trivijalan posao i dosta je manuelan. Prvo treba dohvatiti nove ulice, onda uraditi automatske
izmene u OSM-u, pa onda objaviti nove vektorske mape, pa onda tek možemo da počnemo da ih koristimo.

### Skidanje novih RGZ adresa

Treba da napravite fajl "idp_creds" koji ima dve linije. Prva linija je username, a druga je password za pristup RGZ
sajtu https://download-tmp.geosrbija.rs/download. 

* Bekapovati staru `data/rgz/download` fasciklu (npr. `mkdir <data-datum>; mv *.zip <data-datum>/`) i isprazniti postojeću fasciklu
* Bekapovati stare ulice (`cp data/rgz/streets.csv data/rgz/streets.old.csv`)
* Napraviti fasciklu za nove CSV ulice (`mkdir data/rgz/csv-new`)
* Pokrenuti `python src/download_st_from_rgz`. Skripta smešta .zip fajlove u `data/rgz/download`. Može se pokretati iznova, krenuće tamo gde je stala. Pratiti ukoliko pukne i pokrenuti ponovo. Skripta traje oko 1-2h.
* Proveriti (za svaki slučaj) da imate 168 .zip fajlova u `data/rgz/download` i da nijedan fajl nije prazan (0 bajtova)
* Pokrenuti `python3 src/prepare_rgz_street_data.py --output-csv-file data/rgz/streets.new.csv --output-csv-folder data/rgz/csv-new`. Skripta pravi novi `data/rgz/streets.new.csv` fajl.

### Dopunjavanje pravilnih imena ulica

* Pokrenuti `python3 src/fix_missing_proper_street_names.py` i biće generisan `data/rgz/missing_streets.csv` fajl u kome su sve nove ulice kojima nedostaje pravilno imenovanje.
* Prekopirate ih na dno `ar/curated_streets.csv` i ispraviti sve nazive da budu dobri (Ctrl+F da nađete kako su ranije kapitalizovane neke stvari)
  * Na kraju proveriti standardne greške iz RGZ-a, kao što je trailing space
* Sortirajte curated listu sa `python3 src/sort_curated.streets.py --input-curated-streets ../ar/curated_streets.csv --output-curated-streets curated_streets-sorted.csv`
* Uporedite ih i ako je sve OK, zamenite `ar/curated_streets.csv` sa `curated_streets-sorted.csv`, a `curated_streets-sorted.csv` obrisati.
* Sada izbrisati ar/data/mapping/mapping.csv i regenerisati ga ponovnim pokretanjem `python3 src/street_mapping.py` iz AR modula.

### Automatske izmene u OSM-u

Sad treba da imate fajlove `data/rgz/streets.old.csv` i `data/rgz/streets.new.csv`. Za ovo treba da imate `osm-password` fajl sa kredencijalima za OSM,
kao i lokalni overpass server.

* Izvršiti `python3 src/generate_st_rgz_diff.py --generate` i dobićete 3 fajla: `data/rgz/streets-added.csv` (nove ulice), `data/rgz/streets-removed.csv` (izbrisane ulice) i `data/rgz/streets-changed.csv` (promenjene ulice)
* Izvršiti `python3 src/generate_st_rgz_diff.py --fix_deleted` - prolazi kroz obrisane ulice i ako su stvarno obrisane, briše im `ref:RS:ulica` i dodaje im `removed:ref:RS:ulica`
* Otvoriti  `data/rgz/streets-changed.csv` i naći ćete ulice koje su promenile ime - izmeniti ime u OSM-u.
Najbolje se radi tako što se otvori ovaj fajl u QGIS-u, i ide ulicu po ulicu koje su promenile ime. Ukoliko je stara ulica u OSM-u, učitati ulicu u iD/JOSM i promeniti ime (i staviti i `old_name` takođe).
Ukoliko je u RGZ-u samo pravopisna greška, ne treba stavljati `old_name` (možda eventualno `alt_name` ako mislite da treba).


### Kreiranje vektorske mape

Treba da dobijemo novi `ulice.mbtiles` koji treba staviti na [vektor serveru](https://vector-rgz.openstreetmap.rs/).
Za ovo je potrebno da imamo [tippecanoe](https://github.com/felt/tippecanoe) program instaliran.

* Konvertovati `data/rgz/addresses.new.csv` u geojson:

`ogr2ogr data/rgz/ulice.geojson data/rgz/streets.new.csv -dialect sqlite -sql "SELECT rgz_ulica AS ulica_ime, ST_GeomFromText(rgz_geometry) AS geometry FROM 'streets.new'" -nln ulice`

* Generiše se .mbtiles fajl: `tippecanoe data/rgz/ulice.geojson -o data/rgz/ulice.mbtiles`
* Ovaj fajl se pošalje na vektor server (kredencijale tražiti od autora ovog uputstva)

### Kreiranje rasterske mape

Ovu mapu treba da okačimo na sajt i da obavestimo Peleta da je osveži.

* `ogr2ogr data/rgz/rgz_ulice.shp data/rgz/streets.new.csv -dialect sqlite -sql "SELECT rgz_ulica_mb, rgz_ulica AS rgz_ulica, GeometryFromText(rgz_geometry, 4326) AS geometry FROM 'streets.new'" -lco ENCODING=UTF-8 -s_srs EPSG:4326 -t_srs EPSG:3857`
* `zip -j data/rgz/rgz_ulice_dump_latest.zip data/rgz/rgz_ulice.*`
* `scp data/rgz/rgz_ulice_dump_latest.zip kokanovic:/home/branko/`
* ssh tamo i kopirati ga u fajl sa `rgz_ulice_dump_YYYYMMDD.zip` strukturom, zbog arhiviranja

### Konačna zamena

* Na kraju zameniti stari `data/rgz/streets.csv` sa novim `data/rgz/streets.new.csv` fajlom (`rm data/rgz/streets.csv; mv data/rgz/streets.csv`)
* Zameniti sadržaj `data/rgz/csv` sa sadržajem `data/rgz/csv-new` i obrisati `data/rgz/csv-new`
* Promeniti sadržaj fajla `data/rgz/LATEST`

## Licenca

GPLv3
