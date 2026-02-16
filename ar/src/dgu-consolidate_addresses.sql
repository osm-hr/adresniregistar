SELECT
  a.inspire_id,
  ad.name AS rgz_naselje,
  t.inspire_id AS rgz_ulica_mb,
  t.name AS rgz_ulica,
  a.designators AS rgz_kucni_broj,
  p.postcode AS rgz_postanski_broj,
  a.lat,
  a.lon
FROM 'data/rgz/unzip/Address.csv' AS a
JOIN 'data/rgz/unzip/ThoroughfareName.csv' AS t ON t.gml_id = a.thoroughfare_name_id
JOIN 'data/rgz/unzip/PostalDescriptor.csv' AS p ON p.gml_id = a.postal_descriptor_id
JOIN 'data/rgz/unzip/AdminUnitName.csv' AS ad ON ad.gml_id = a.admin_unit_1
