SELECT
  regexp_replace(a.inspire_id, '^HS\.', '') AS rgz_kucni_broj_id,
  o.opstina_maticni_broj AS rgz_opstina_mb,
  o.opstina_imel AS rgz_opstina,
  ad.inspire_id AS rgz_naselje_mb,
  ad.name AS rgz_naselje,
  ad.inspire_id AS rgz_naselje_inspire_id,
  t.inspire_id AS rgz_ulica_mb,
  t.name AS rgz_ulica,
  a.designators AS rgz_kucni_broj,
  p.postcode AS rgz_postanski_broj,
  'POINT (' || a.lon || ' ' || a.lat || ')' AS rgz_geometry
FROM 'data/rgz/unzip/Address.csv' AS a
JOIN 'data/rgz/unzip/ThoroughfareName.csv' AS t ON t.gml_id = a.thoroughfare_name_id
JOIN 'data/rgz/unzip/PostalDescriptor.csv' AS p ON p.gml_id = a.postal_descriptor_id
JOIN 'data/rgz/unzip/AdminUnitName.csv' AS ad ON ad.gml_id = a.admin_unit_1
JOIN 'data/rgz/opstina.csv' AS o ON regexp_replace(o.inspire_id, '^AU\.', '') = regexp_replace(a.admin_unit_2, '^SI\.GURS\.RPE\.', '')
