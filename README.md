# AdresniRegistar

## Instalacija

Pokrenuti `python3 -m pip install -r requirements.txt` za instalaciju svih zavisnosti.

Treba skinuti i [`geckodriver` binary](https://github.com/mozilla/geckodriver/releases) i staviti ga u root projekta.

## Korišćenje

Sve komande se izvršavaju sa `make <komanda>`. Dostupne su sledeće komande:
* `clean`
  
  Briše sve sakupljene i generisane fajlove da se proces počne iz početka


* `download_from_rgz`

  Da biste koristili ovu komandu, treba da napravite fajl "rgz_creds" koji ima dve linije. Prva linija je username,
  a druga je password za pristup RGZ sajtu https://download-tmp.geosrbija.rs/download.
  
  Komanda skida sve kućne brojeve svih opština sa RGZ sajta i smešta ih u data/rgz_opstine/download. 
  Ukoliko je neka opština već tu, preskače skidanje. Zatim otpakuje sve zipove, reprojektuje EPSG:32634 u WSG84 i
  pravi data/all_addressess.csv koji se koristi u daljem radu.

## Licenca

GPLv3
