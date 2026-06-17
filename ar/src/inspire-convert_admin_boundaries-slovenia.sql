SELECT
  o.opstina_maticni_broj AS object_id,
  o.opstina_maticni_broj AS naselje_maticni_broj,
  o.opstina_imel AS naselje_ime,
  o.opstina_imel AS naselje_imel,
  '0' AS naselje_povrsina,
  o.opstina_maticni_broj AS opstina_maticni_broj,
  o.opstina_ime AS opstina_ime,
  o.opstina_imel AS opstina_imel,
  o.geometry AS wkt
FROM 'data/rgz/opstina.csv' AS o
