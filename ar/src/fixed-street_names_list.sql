SELECT rgz_ulica AS name FROM (SELECT DISTINCT rgz_ulica FROM read_csv_auto('data/rgz/addresses.csv'))
WHERE rgz_ulica NOT IN (SELECT rgz_name FROM read_csv_auto('curated_streets.csv'))
UNION
SELECT name FROM read_csv_auto('curated_streets.csv')
WHERE rgz_name IN (SELECT rgz_ulica FROM read_csv_auto('data/rgz/addresses.csv'))
