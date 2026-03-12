SELECT
  n.objectid AS object_id,
  n.naselje_maticni_broj AS naselje_maticni_broj,
  n.naselje_ime AS naselje_ime,
  n.naselje_imel AS naselje_imel,
  n.naselje_povrsina AS naselje_povrsina,
  o.opstina_maticni_broj AS opstina_maticni_broj,
  o.opstina_ime AS opstina_ime,
  o.opstina_imel AS opstina_imel,
  n.wkt AS wkt
FROM 'data/rgz/naselja.csv' AS n
JOIN 'data/rgz/opstina.csv' AS o ON o.inspire_id = n.opstina_inspire_id