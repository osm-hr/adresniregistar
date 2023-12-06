# -*- coding: utf-8 -*-

import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from shapely import wkt


def is_circle(geom) -> bool:
    if geom.geom_type == 'LineString':
        length = geom.length
        end_distance = shapely.Point(geom.coords[0]).distance(shapely.Point(geom.coords[-1]))
        if end_distance < 0.2 * length:  # 20% of length
            return True
        return False
    if geom.geom_type != 'MultiLineString':
        print(f"Unknown geometry {geom.geom_type}, treating it as non-circle")
        return False

    geometries = list(shapely.get_parts(geom))

    if len(geometries) >= 100:  # This is cutoff for what we thing circle geometry can be in RGZ. This speeds up this O(N^2) calculations
        return False

    # We iterate for all LineStrings in this MultiLineString. We check each pair of LineString and compare them to see
    # if they are close enough (20m). If they are, we connect them. If they do not merge all to one LineString, this is
    # not considered a circle. If we can string them altogether, we check for circle.
    #
    # Some people suggested that we can order all
    # endpoints and put them in some spatial index, sort that and we might get O(N logN) behaviour.
    while True:
        min_distance = None
        geom1_idx, geom2_idx = None, None
        direction = None
        for i in range(len(geometries)):
            for j in range(i):
                distance = shapely.Point(geometries[i].coords[0]).distance(shapely.Point(geometries[j].coords[0]))
                if distance < 20 and (min_distance is None or (distance < min_distance)):
                    min_distance = distance
                    geom1_idx = i
                    geom2_idx = j
                    direction = 0
                distance = shapely.Point(geometries[i].coords[0]).distance(shapely.Point(geometries[j].coords[-1]))
                if distance < 20 and (min_distance is None or (distance < min_distance)):
                    min_distance = distance
                    geom1_idx = i
                    geom2_idx = j
                    direction = 1
                distance = shapely.Point(geometries[i].coords[-1]).distance(shapely.Point(geometries[j].coords[0]))
                if distance < 20 and (min_distance is None or (distance < min_distance)):
                    min_distance = distance
                    geom1_idx = i
                    geom2_idx = j
                    direction = 2
                distance = shapely.Point(geometries[i].coords[-1]).distance(shapely.Point(geometries[j].coords[-1]))
                if distance < 20 and (min_distance is None or (distance < min_distance)):
                    min_distance = distance
                    geom1_idx = i
                    geom2_idx = j
                    direction = 3
                if min_distance == 0.0:
                    break
            if min_distance == 0.0:
                break
        if min_distance is None:  # we didn't found any candidate for merging, bail out
            break
        if direction == 0:
            new_line = shapely.linestrings(list(geometries[geom1_idx].coords)[::-1] + list(geometries[geom2_idx].coords))
        elif direction == 1:
            new_line = shapely.linestrings(list(geometries[geom1_idx].coords)[::-1] + list(geometries[geom2_idx].coords)[::-1])
        elif direction == 2:
            new_line = shapely.linestrings(list(geometries[geom1_idx].coords) + list(geometries[geom2_idx].coords))
        else:
            new_line = shapely.linestrings(list(geometries[geom1_idx].coords) + list(geometries[geom2_idx].coords)[::-1])
        geometries.pop(geom1_idx)
        geometries.pop(geom2_idx)
        geometries = shapely.multilinestrings(geometries + [new_line, ])
        geometries = list(shapely.get_parts(geometries))
    if len(geometries) > 1:
        # We didn't manage to merge linestrings, bailing out
        return False
    return is_circle(geometries[0])


def is_circles(thread_index, df):
    result_dict = {}
    total_count = len(df)
    for i, iterrow in enumerate(df.iterrows()):
        if i % 1000 == 0:
            print(f"[{thread_index}] {i}/{total_count}")
        result_dict[iterrow[1]['rgz_ulica_mb']] = is_circle(iterrow[1]['rgz_geometry'])
    print(f"[{thread_index}] done")
    return result_dict


def main():
    cwd = os.getcwd()
    rgz_path = os.path.join(cwd, 'data/', 'rgz/')

    input_rgz_file = os.path.join(rgz_path, f'streets.csv')

    if os.path.exists(os.path.join(rgz_path, f'cache_circle.csv')):
        print(f"    Skipping creation of cache_circle, already exists")
        return

    print(f"Loading RGZ streets")
    df_rgz = pd.read_csv(input_rgz_file)
    df_rgz['rgz_geometry'] = df_rgz.rgz_geometry.apply(wkt.loads)
    gdf_rgz = gpd.GeoDataFrame(df_rgz, geometry='rgz_geometry', crs="EPSG:4326")

    gdf_rgz.to_crs("EPSG:32634", inplace=True)
    all_futures = []
    result_dict = {}
    thread_count = max(multiprocessing.cpu_count() // 2, 1)
    duplicates = gdf_rgz['rgz_ulica_mb'].duplicated()
    if len(duplicates[duplicates == True]) > 0:
        print(f"There are {len(duplicates[duplicates == True])} duplicates in rgz_ulica_mb, cannot continue as algorithm do not support this")
        raise Exception

    gdf_rgz_split = np.array_split(gdf_rgz, thread_count)
    with ProcessPoolExecutor(max_workers=thread_count) as executor:
        for i in range(thread_count):
            future = executor.submit(is_circles, i+1, gdf_rgz_split[i])
            all_futures.append(future)
        for future in as_completed(all_futures):
            result_dict = {**result_dict, **future.result()}

    result_dict[791067121580] = False  # ТРГ ПРИЈАТЕЉСТВА СРБИЈЕ И КИНЕ
    result_dict[791105011877] = False  # СТУДЕНТСКИ ТРГ
    result_dict[791105112807] = False  # ТРГ РЕПУБЛИКЕ
    result_dict[791105005339] = False  # КОПИТАРЕВА ГРАДИНА
    result_dict[791024115496] = False  # ТРГ СЛАВИЈА
    result_dict[791024134270] = False  # СКВЕР МИЛЕНЕ И ГАГЕ
    result_dict[704652160019] = False  # ТРГ САШЕ РАДИШИЋА
    result_dict[704741061757] = False  # КРАЉА МИЛУТИНА
    result_dict[704563058459] = False  # РАДНИЧКА
    result_dict[704741065803] = False  # ВЛАДЕ АКСЕНТИЈЕВИЋА
    result_dict[704741065802] = False  # БОЖИДАРА ФЕРЈАНЧИЋА
    result_dict[704741065801] = False  # ЛИВАДСКА
    result_dict[704741065800] = False  # ЦИГЛАНСКА # TODO: why this is circle?
    result_dict[704741065799] = False  # ВИДОВДАНСКА
    result_dict[803138100017] = False  # ТРГ КРАЉА ПЕТРА I
    result_dict[803138100005] = False  # ТРГ СЛОБОДЕ
    result_dict[803138101001] = False  # ТРГ ЂОРЂА ВАЈФЕРТА
    result_dict[803138125252] = False  # ТРГ ДР ЗОРАНА ЂИНЂИЋА
    result_dict[803138100290] = False  # ТРГ XII ВОЈВОЂАНСКЕ БРИГАДЕ
    result_dict[802832100826] = False  # ТРГ ВЛАДИКЕ НИКОЛАЈА
    result_dict[802824101608] = False  # ТРГ ФЕХЕР ФЕРЕНЦА
    result_dict[802824100100] = False  # ТРГ ГАЛЕРИЈА
    result_dict[802824100321] = False  # ТРГ МЛАДЕНАЦА
    result_dict[802824100624] = False  # ТРГ СЛОБОДЕ
    result_dict[802824000627] = False  # ТРИФКОВИЋЕВ ТРГ
    result_dict[802824124132] = False  # ТРГ САВЕ ВУКОСАВЉЕВА
    result_dict[802824100617] = False  # ТРГ КОМЕНСКОГ
    result_dict[802824001894] = False  # СИМЕ ЋИРКОВИЋА
    result_dict[802824001802] = False  # ЈЕФТЕ ТЕШИЋА
    result_dict[802824002204] = False  # МАРИЈЕ КАЛАС
    result_dict[804479000007] = False  # БАЧКИ ВИНОГРАДИ САЛАШИ
    result_dict[803979090166] = False  # МАЛА БОСНА
    result_dict[801542000307] = False  # ПАРИСКЕ КОМУНЕ
    result_dict[801542000204] = False  # КОСТЕ ТУРКУЉА
    result_dict[801542000164] = False  # ЈАНКА ВЕСЕЛИНОВИЋА
    result_dict[801496100017] = False  # ТРГ НАРОДНОГ ХЕРОЈА Д. ЋУБИЋА
    result_dict[746606000274] = False  # ТИРШОВ ВЕНАЦ
    result_dict[746606100352] = False  # ТРГ СТАНИСЛАВА ВИНАВЕРА
    result_dict[800767000121] = False  # АУТО КАМП НОВА
    result_dict[704466054230] = False  # ВЕСЕ ПЕТРОВИЋА
    result_dict[725579000051] = False  # ШЕКСПИРОВА
    result_dict[725480000106] = False  # ЈУГ БОГДАНА
    result_dict[725552100231] = False  # ТРГ ВУКА КАРАЏИЋА
    result_dict[725552100230] = False  # ТРГ ЈОВАНА ЦВИЈИЋА
    result_dict[708402300256] = False  # НАСЕЉЕ СРЕТЕНА ДУДИЋА
    result_dict[708402300255] = False  # НАСЕЉЕ МИЛИВОЈА БЈЕЛИЦЕ
    result_dict[708402000730] = False  # СЕЊАК
    result_dict[708402300798] = False  # НАСЕЉЕ ЗБРАТИМЉЕНИ ГРАДОВИ
    result_dict[708402100824] = False  # ТРГ ВЛАДИКЕ НИКОЛАЈА
    result_dict[740527000018] = False  # БАРСКА
    result_dict[733083000026] = False  # ПИОНИРСКИ ТРГ
    result_dict[733083000004] = False  # БРАНИЧЕВСКИ СКВЕР
    result_dict[706418080031] = False  # ВЕЛИМИРА СИМОНОВИЋА
    result_dict[706477010098] = False  # ТАУШАНОВИЋ ДРАГАНА ЦИЦИ
    result_dict[706477010094] = False  # ЈОВАНА ГРАМИЋА
    result_dict[713325010047] = False  # ЂЕНЕРАЛА МИЛИЋА
    result_dict[718980013431] = False  # БАНА ЈАНИЋИЈА КРАСОЈЕВИЋА
    result_dict[715689000011] = False  # БРАНКА ПЕРИЋА
    result_dict[706507000007] = False  # КОТ
    result_dict[731501000118] = False  # ДОСТОЈЕВСКОГ
    result_dict[741892000515] = False  # ВЕЛЕШКА
    result_dict[741892000261] = False  # ТАКОВСКА
    result_dict[719714000404] = False  # МИЛУТИНА МИЛОШЕВИЋА
    result_dict[719714000228] = False  # ПИЛОТА ПОТПУКОВНИКА ЖИВОТЕ ЂУРИЋА
    result_dict[719714000111] = False  # ДРАГИЋА ПАНТОВИЋА ПАТКА
    result_dict[719714000163] = False  # СВЕТЕ ТРОЈИЦЕ
    result_dict[719714001121] = False  # ЦВЕТКА СТОЈАНОВИЋА ПЕКАРА
    result_dict[719714001213] = False  # СТАНИСЛАВА СРЕМЧЕВИЋА ЦРНОГ
    result_dict[719684000031] = False  # СВЕТОГ ВАСИЛИЈА ОСТРОШКОГ
    result_dict[719684000032] = False  # СВЕТОГ АРХАНГЕЛА МИХАИЛА
    result_dict[719684000033] = False  # СВЕТЕ ПЕТКЕ
    result_dict[719684000034] = False  # СВЕТОГ ЂОРЂА
    result_dict[720062000092] = False  # ЈОВАНА САРИЋА
    result_dict[719684000030] = False  # СВЕТОГ НИКОЛЕ
    result_dict[720291000056] = False  # ПЕТРА БОЈОВИЋА
    result_dict[719706000039] = False  # КРАЉА ПЕТРА ПРВОГ
    result_dict[746649000058] = False  # АРЧИБАЛДА РАЈСА
    result_dict[746649000036] = False  # МИЛАНА МИЛОВАНОВИЋА
    result_dict[746649000038] = False  # ЛАЗЕ РИСТОВСКОГ
    result_dict[746649000044] = False  # МИЛОРАДА ЈОКСИМОВИЋА ПИЛИВИКЕ
    result_dict[746649000046] = False  # БАШТОВАНСКА
    result_dict[792012090004] = False  # БУЛЕВАР ПОТПУКОВНИКА ГОРАНА ОСТОЈИЋА
    result_dict[792055030051] = False  # НОВА ЖЕЛЕЗНИЧКА КОЛОНИЈА
    result_dict[792047029935] = False  # ЖАРКА ЂУРИЋА
    result_dict[792047030043] = False  # ДРУГОГ СРПСКОГ УСТАНКА
    result_dict[711306100448] = False  # ТРГ РЕПУБЛИКЕ
    result_dict[711926010002] = False  # ДРАГОЉУБА МИХАЈЛОВИЋА
    result_dict[707694000021] = False  # ВРБАНСКА
    result_dict[707694000032] = False  # НАСЕЉЕ МОРАВА 76
    result_dict[737178100070] = False  # ТРГ ЈОСИФА ПАНЧИЋА
    result_dict[741744000040] = False  # ТАНАСКА РАЈИЋА
    result_dict[720526010066] = False  # ЂУРЕ ЈАКШИЋА

    df_circle = pd.DataFrame(result_dict.items(), columns=['rgz_ulica_mb', 'is_circle'])
    pd.DataFrame(df_circle).to_csv(os.path.join(rgz_path, f'debug_cache_circle_all.csv'), index=False)

    input_rgz_file = os.path.join(rgz_path, f'streets.csv')
    df_rgz = pd.read_csv(input_rgz_file, dtype={'rgz_ulica_mb': str})
    df_rgz['rgz_geometry'] = df_rgz.rgz_geometry.apply(wkt.loads)
    gdf_rgz = gpd.GeoDataFrame(df_rgz, geometry='rgz_geometry', crs="EPSG:4326")
    gdf_rgz = gdf_rgz.merge(df_circle, on=['rgz_ulica_mb'], how='left')
    pd.DataFrame(gdf_rgz).to_csv(os.path.join(rgz_path, f'debug_rgz_with_cached_circle.csv'), index=False)

    df_circle = df_circle[df_circle.is_circle == True]
    pd.DataFrame(df_circle).to_csv(os.path.join(rgz_path, f'cache_circle.csv'), index=False)


if __name__ == '__main__':
    main()
