# -*- coding: utf-8 -*-

from enum import Enum


cyr_to_lat = {
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E',
    'Ж': 'Ž', 'З': 'Z', 'И': 'I', 'Ј': 'J', 'К': 'K', 'Л': 'L',
    'М': 'M', 'Н': 'N', 'Њ': 'NJ', 'О': 'O', 'П': 'P', 'Р': 'R',
    'С': 'S', 'Т': 'T', 'Ћ': 'Ć', 'У': 'U', 'Ф': 'F', 'Х': 'H',
    'Ц': 'C', 'Ч': 'Č', 'Џ': 'DŽ', 'Ш': 'Š', 'Ђ': 'Đ', 'Љ': 'LJ',
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e',
    'ж': 'ž', 'з': 'z', 'и': 'i', 'ј': 'j', 'к': 'k', 'л': 'l',
    'љ': 'lj','м': 'm', 'н': 'n', 'њ': 'nj', 'о': 'o', 'п': 'p',
    'р': 'r', 'с': 's', 'т': 't', 'ћ': 'ć', 'у': 'u', 'ф': 'f',
    'х': 'h', 'ц': 'c', 'ч': 'č', 'џ': 'dž', 'ш': 'š', 'ђ': 'đ'
}


def cyr2lat(text):
    if type(text) == int:
        return str(text)
    out = ''
    for c in text:
        if c in cyr_to_lat:
            out += cyr_to_lat[c]
        else:
            out += c
    return out


class ApartmentResolution(Enum):
    OSM_ENTITY_NOT_FOUND = 1  # recently deleted or recently added
    NODE_DETACHED = 2  # node is detached, cannot be building=apartments
    OSM_ENTITY_NOT_BUILDING = 3  # If entity is node, it is attached to something that is not tagged as building. If it is way or relation, it is not tagged as building
    OSM_ENTITY_NOT_APARTMENT = 4  # If entity is node, it is attached to something that is not tagged as building=apartments. If it is way or relation, it is not tagged as building=apartments
    OSM_ENTITY_APARTMENT = 5  # All is OK
