import csv
import geopandas as gpd
import pandas as pd
from pathlib import Path

shp_path = Path('./data/rgz/unzip/RPJ_MO.shp')
naselje_path = Path('./data/rgz/naselje.csv')
addresses_path = Path('./data/rgz/addresses.csv')

gdf = gpd.read_file(shp_path).to_crs('EPSG:3035')
gdf['JMS_IME'] = gdf['JMS_IME'].str.strip('"')
# --- Update naselje.csv ---

naselje_df = pd.read_csv(naselje_path)
naselje_df = naselje_df[naselje_df['opstina_maticni_broj'] != 1333]

new_naselja = pd.DataFrame({
    'object_id': 0,
    'naselje_maticni_broj': gdf['JMS_MB'].astype(int),
    'naselje_ime': gdf['JMS_IME'],
    'naselje_imel': gdf['JMS_IME'],
    'naselje_povrsina': gdf['Shape_Area'],
    'opstina_maticni_broj': 1333,
    'opstina_ime': 'Grad Zagreb',
    'opstina_imel': 'Grad Zagreb',
    'wkt': gdf.geometry.to_wkt(),
})

naselje_df = pd.concat([naselje_df, new_naselja], ignore_index=True)
naselje_df.to_csv(naselje_path, index=False, encoding='utf-8')
print(f"naselje.csv: {len(new_naselja)} new rows added, total {len(naselje_df)}")

# --- Update addresses.csv ---

addr_df = pd.read_csv(addresses_path)
zagreb_mask = addr_df['rgz_opstina_mb'] == 1333
zagreb_addr = addr_df[zagreb_mask].copy()

zagreb_gdf = gpd.GeoDataFrame(
    zagreb_addr,
    geometry=gpd.GeoSeries.from_wkt(zagreb_addr['rgz_geometry']),
    crs='EPSG:4326',
)
gdf_wgs84 = gdf[['JMS_MB', 'JMS_IME', 'MBR_NADR', 'geometry']].to_crs('EPSG:4326')

joined = gpd.sjoin(zagreb_gdf, gdf_wgs84, how='left', predicate='within')

unmatched_mask = joined['JMS_MB'].isna()
if unmatched_mask.any():
    nearest = gpd.sjoin_nearest(zagreb_gdf[unmatched_mask], gdf_wgs84, how='left')
    joined.loc[unmatched_mask, 'JMS_MB'] = nearest['JMS_MB'].values
    joined.loc[unmatched_mask, 'JMS_IME'] = nearest['JMS_IME'].values
    joined.loc[unmatched_mask, 'MBR_NADR'] = nearest['MBR_NADR'].values
    print(f"{unmatched_mask.sum()} border addresses resolved via nearest polygon")

addr_df.loc[zagreb_mask, 'rgz_naselje_mb'] = joined['JMS_MB'].astype('Int64').values
addr_df.loc[zagreb_mask, 'rgz_naselje'] = joined['JMS_IME'].values

addr_df.to_csv(addresses_path, index=False, encoding='utf-8', quoting=csv.QUOTE_NONNUMERIC)
print(f"addresses.csv: {zagreb_mask.sum()} Zagreb addresses updated")
