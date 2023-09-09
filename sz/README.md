# Registar stambenih zajednica

## Instalacija

Pokrenuti `python3 -m pip install -r requirements.txt` za instalaciju svih zavisnosti.


Za sad treba skinuti i .ods fajl sa https://data.gov.rs/sr/datasets/registar-stambenikh-zajednitsa-2/ i sačuvati ga u `data/registarstambenihzajednica.csv`.

## Korišćenje

Za generisanje `data/sz_analysis.csv` (izlaz analize) možete pokrenuti `python3 src/sz_analysis.py --data-path <putanja>`.

`--data-path` je putanja do `ar/` direktorijuma gde se nalaze već generisani fajlovi (pogledajti [README.md](../ar/README.md) ar/ projekta).

Kada imate `data/sz_analysis.csv`, možete pokrenuti `python3 src/report.py` da izgenerišete HTML fajlove u `output/` direktorijumu.

Postoji i skripta `run.sh` koja radi sve ovo i upload-uje na server.


## Licenca

GPLv3
