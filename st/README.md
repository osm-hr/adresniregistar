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

## Licenca

GPLv3
