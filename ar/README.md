# AdresniRegistar

## Instalacija

Pokrenuti `python3 -m pip install -r requirements.txt` za instalaciju svih zavisnosti.

Treba skinuti i [`geckodriver` binary](https://github.com/mozilla/geckodriver/releases) i staviti ga u root projekta.

Treba da imate i `parallel` program (na Debian-u se prosto instalira sa `sudo apt install parallel`).

Pored toga u direktorijum data/rgz treba skinuti sa opendata.geosrbija.rs opstina.csv i naselje.csv.

Za sad treba skinuti i opstina.zip sa https://opendata.geosrbija.rs (dok se ne automatizuje) i otpakovati opstina.csv u data/rgz direktorijum.

## Korišćenje

Sve komande se izvršavaju sa `make <komanda>`. Dostupne su sledeće komande:


* `clean`
  
  Briše sve sakupljene i generisane fajlove da proces počne iz početka


* `download_from_osm`

  Ova komanda skida najnoviji PBF Srbije sa geofabrika, izvlači sve adrese sa teritorije Srbije koje postoje u OSM-u,
  i deli sve adrese po opštinama. Te adrese završe u data/osm/csv, a napravi se i globalna u data/osm/addresses.csv.
  
  
* `normalize_street_names`

  Ova komanda prolazi kroz sve RGZ ulice i pokušava da od formata gde su sve ulice velikim slovom (npr. "ПЕТРА ДРАПШИНА")
  pretvori heuristikom u gramatički ispravan format ("Петра Драпшина"). Izlaz se zapisuje u fajl data/mapping/mapping.csv
  gde imamo ulicu iz RGZ-a velikim slovima, ulicu kako se pravilno piše, i način kako smo došli do ovoga zaključka i koje
  ulice iz OSM-a su dovele do ove odluke (radi debagovanja). Naravno, ovaj ceo proces ima grešaka i ovo je best effort
  heuristika. Za heuristiku se koristi fajl "curated_streets.csv" gde mogu da se ubace sve što želimo odmah da prebacimo
  ručno (override-ujemo heuristiku). Zatim se koristi OSM podaci da se nađu te ulice preko "ref:RS:ulica" taga jer
  pretpostavljamo da su u OSM-u unete dobro. Posle toga se koristi i OSM podaci bez "ref:RS:ulica" taga gde se koristi
  normalizacija ulica iz RGZ-a i OSM-a da se one match-uju i da proba tako da se nađe kako se ulica pravilno piše.
  Ako ni to ne uspe, algoritam uskače i pokušava, što je bolje moguće da pravilno napiše ulicu. Naravno, greške su neminovne.


* `analyze`

  Ova komanda uzme podatke iz OSM-a i RGZ-a i obrađuje adrese po opštinama. Za svaku RGZ adresu pokušava da pronađe odgovarajuću
  adresu u OSM-u. Takva adresa može da se nađe (postavi se "`matching`" kolona na `True`), a ako se ne nađe, pokušava da nađe
  najpribližniju adresu u radijusu od 200m na osnovu imena ulice, kućnog broja i udaljenosti RGZ i OSM adresa. Ukoliko nađe
  takvu adresu, postavlja se "`score``" i OSM elementi, a ako nema, te kolone ostaju prazne. Rezultujući CSV se smešta u
  data/analasis direktorijum.


* `quality_assurance`

  Ova komanda radi razne analize koje se posle koriste prilikom generisanja report-a. Trenutno se rade dve analize:
  * ref:RS:kucni_broj duplikati - nalazimo sve kućne brojeve koji imaju dupli `ref:RS:kucni_broj` tag
  * analiza adresa unutar zgrada. Ukoliko imamo adresu ili POI koji je unutar zgrade (way-a building-a), detektujemo ga
  ovde i pokušavamo da uradimo kategorizaciju, tj. da vidimo da li je ovo OK ili nije, i ako nije, šta možemo da uradimo
  ovo ovoga.


* `report`

  Ova komanda generiše HTML fajlove u `data/report` direktorijumu na osnovu prethodno urađene analize. Izgenerisani
  fajlovi su statički i mogu se prebaciti na neki server. Veličina je velika, 800 MB neotpakovano, 80 MB zapakovano. 

* `upload_report`

  Ova komanda uploaduje izgenerisane HTML fajlove na DINA platformu.

## Osvežavanje sa RGZ-a

Osvežavanje nije trivijalan posao i dosta je manuelan. Prvo treba dohvatiti nove adrese, onda uraditi automatske
izmene u OSM-u, pa onda objaviti nove vektorske mape, pa onda tek možemo da počnemo da ih koristimo.

Savetuje se da se u isto vreme radi ažuriranje i ulica i adresa (kućnih brojeva) i to tako što se prvo uradi ažuriranje ulica
(zato što se tad popunjuvaju pravilna imena novododatih ulica)!

### Skidanje novih RGZ adresa

Treba da napravite fajl "idp_creds" koji ima dve linije. Prva linija je username, a druga je password za pristup RGZ
sajtu https://download-tmp.geosrbija.rs/download. 

* Bekapovati staru `data/rgz/download` fasciklu (npr. `mkdir <data-datum>; mv *.zip <data-datum>/`)
* Bekapovati stare adrese (`cp data/rgz/addresses.csv data/rgz/addresses.old.csv`)
* Napraviti fasciklu za nove CSV adrese (`mkdir data/rgz/csv-new`)
* Pokrenuti `python src/download_from_rgz`. Skripta smešta .zip fajlove u `data/rgz/download`. Može se pokretati iznova, krenuće tamo gde je stala. Pratiti ukoliko pukne i pokrenuti ponovo. Skripta traje oko 1-2h.
* Proveriti (za svaki slučaj) da imate 168 .zip fajlova u `data/rgz/download` i da nijedan fajl nije prazan (0 bajtova)
* Pokrenuti `python3 src/prepare_rgz_data.py --output-csv-file data/rgz/addresses.new.csv --output-csv-folder data/rgz/csv-new`. Skripta pravi novi `data/rgz/addresses.new.csv` fajl.

### Automatske izmene u OSM-u

Sad treba da imate fajlove `data/rgz/addresses.old.csv` i `data/rgz/addresses.new.csv`. Za ovo treba da imate `osm-password` fajl sa kredencijalima za OSM,
kao i lokalni overpass server.

* Izvršiti `python3 src/generate_rgz_diff.py --generate` i dobićete 3 fajla: `data/rgz/addresses-added.csv` (nove adrese), `data/rgz/addresses-removed.csv` (izbrisane adrese) i `data/rgz/addresses-changed.csv` (promenjene adrese)
* Učitati `data/rgz/addresses-added.csv` i `data/rgz/addresses-removed.csv` i videti da izbrisana ulica nije zamenjena nekom novom ulicom
* Izvršiti `python3 src/generate_rgz_diff.py --fix_deleted_to_added --rgz_update_date YYYY-MM-DD` - prolazi kroz obrisane adrese i ako su stvarno obrisane, briše im `ref:RS:kucni_broj` i dodaje im `removed:ref:RS:kucni_broj`, a ako su dodate sa novim ID-om, menja `ref:RS:kucni_broj`
* Izvršiti `python3 src/generate_rgz_diff.py --fix_changed` - prolazi kroz promenjene adrese i menja ih u OSM-u sa novim vrednostima

### Kreiranje vektorske mape

Treba da dobijemo novi `adrese.mbtiles` koji treba staviti na [vektor serveru](https://vector-rgz.openstreetmap.rs/).
Za ovo je potrebno da imamo [tippecanoe](https://github.com/felt/tippecanoe) program instaliran.

* Konvertovati `data/rgz/addresses.new.csv` u geojson:

`ogr2ogr data/rgz/adrese.geojson data/rgz/addresses.new.csv -dialect sqlite -sql "SELECT rgz_kucni_broj, ST_GeomFromText(rgz_geometry) AS geometry FROM 'addresses.new'" -nln adrese`

* Generiše se .mbtiles fajl: `tippecanoe data/rgz/adrese.geojson -o data/rgz/brojevi.mbtiles --force`
* Ovaj fajl se pošalje na vektor server (kredencijale tražiti od autora ovog uputstva)

### Kreiranje rasterske mape

Ovu mapu treba da okačimo na sajt i da obavestimo Peleta da je osveži.

* `ogr2ogr data/rgz/rgz_adrese.shp data/rgz/addresses.new.csv -dialect sqlite -sql "SELECT rgz_ulica, rgz_kucni_broj, GeometryFromText(rgz_geometry, 4326) AS geometry FROM 'addresses.new'" -lco ENCODING=UTF-8 -s_srs EPSG:4326 -t_srs EPSG:3857`
* `zip -j data/rgz/rgz_adrese_dump_latest.zip data/rgz/rgz_adrese.*`
* `scp data/rgz/rgz_adrese_dump_latest.zip kokanovic:/home/branko/`
* ssh tamo i kopirati ga u fajl sa `rgz_ulice_dump_YYYYMMDD.zip` strukturom, zbog arhiviranja

### Konačna zamena

* Na kraju zameniti stari `data/rgz/addresses.csv` sa novim `data/rgz/addresses.new.csv` fajlom (`rm data/rgz/addresses.csv; mv data/rgz/addresses.csv`)
* Zameniti sadržaj `data/rgz/csv` sa sadržajem `data/rgz/csv-new` i obrisati `data/rgz/csv-new`
* Promeniti sadržaj fajla `data/rgz/LATEST`

## Licenca

GPLv3
