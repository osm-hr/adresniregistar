# AdresniRegistar

## Instalacija

Pokrenuti `python3 -m pip install -r requirements.txt` za instalaciju svih zavisnosti.

Treba skinuti i [`geckodriver` binary](https://github.com/mozilla/geckodriver/releases) i staviti ga u root projekta.

Za sad treba skinuti i opstina.zip sa https://opendata.geosrbija.rs (dok se ne automatizuje) i otpakovati opstina.csv u data/rgz direktorijum.

## Korišćenje

Sve komande se izvršavaju sa `make <komanda>`. Dostupne su sledeće komande:
* `clean`
  
  Briše sve sakupljene i generisane fajlove da proces počne iz početka


* `download_from_rgz`

  Da biste koristili ovu komandu, treba da napravite fajl "idp_creds" koji ima dve linije. Prva linija je username,
  a druga je password za pristup RGZ sajtu https://download-tmp.geosrbija.rs/download.
  
  Komanda skida sve kućne brojeve svih opština sa RGZ sajta i smešta ih u data/rgz/download. 
  Ukoliko je neka opština već tu, preskače skidanje. Zatim otpakuje sve zipove, reprojektuje EPSG:32634 u WSG84 i
  pravi data/rgz/addressess.csv sa svim adresama, kao i CSV-ove po opštinama u data/rgz/csv/ koji se koriste u daljem radu.


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


* `report`

  Ova komanda generiše HTML fajlove u `data/report` direktorijumu na osnovu prethodno urađene analize. Izgenerisani
  fajlovi su statički i mogu se prebaciti na neki server. Veličina je velika, 800 MB neotpakovano, 80 MB zapakovano. 


## Licenca

GPLv3
