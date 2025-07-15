"""Contains translations to be used in models.py"""

WIND_SCALE_8 = {
    '-': 0,  # Штиль
    'Šiaurės': 1,  # North +
    'Pietų': 5,  # South +
    'Rytų': 3,  # East +
    'Vakarų': 7,  # West +
    'Šiaurės vakarų': 8,  # Northwest +
    'Šiaurės rytų': 2,  # Northeast +
    'Pietvakarių': 6,  # Southwest +
    'Pietryčių': 4  # Southeast +
}

WIND_DEGREES = {
    '-': None,
    'Šiaurės': 0,  # 0 North +
    'Pietų': 180,  # 180 South +
    'Rytų': 90,  # 90  East +
    'Vakarų': 270,  # 270  West +
    'Šiaurės vakarų': 315,  # 315  Northwest +
    'Šiaurės rytų': 45,  # 45  Northeast +
    'Pietvakarių': 225,  # 225  Southwest +
    'Pietryčių': 135  # 135  Southeast +
}

SURFACE_CONDITIONS = {
    'name': 'SURFACE_CONDITIONS',
    'Sausa': 11,  # 11 Dry. Сухая. +
    'Šlapia': 51,  # 51 Wet. Влажная. -
    'Drėgna': 12,  # 12  Slightly wet. Слегка влажная. -
    'Klaida': 00,  # 00 Ошибка станции. +
    'Pažliugęs sniegas': 13,  # Немного воды и снега ?
    'Sniegas': 14,  # Снежный налет ?
    'Ledas': 71  # Гололедица ?
}
# коды Литва. Справа найденный код соответствия по 4680 / дословный перевод / Расшифровка по 4680.
PRECIPITATION_TYPES = {
    'name': 'PRECIPITATION_TYPES',
    'Nėra (p. pask. val. krituliai)': 21,  # 21+ None (precipitation past hour) / Drizzle (not freezing) or snow grains
    'Nėra (p. pask. val. lietus)': 23,  # 23+ None (rain past hour) / Rain (not freezing)
    'Nėra (p. pask. val. dulksna)': 10,  # 10+ None (mist past hour) / Mist
    'Nėra (p. pask. val. rūkas)': 20,  # 20+ None (fog past hour) / PRECIPITATION
    'Rūkas': 30,  # 30+ Fog / FOG
    'Rūkas arba ledo rūkas, nepasikeitė per paskutinę valandą': 33,  # 33+ Fog, or ice fog, has not changed in the last hour / Fog or ice fog, no appreciable change during the past hour
    'Rūkas arba ledo rūkas, sumažėjo per paskutinę valandą': 32,  # 32+ The fog, or ice fog, has subsided in the last hour / Fog or ice fog, has become thinner during the past hour
    'Rūkas arba ledo rūkas, ruožais': 31,  # 31+ Fog or ice fog, in patches / Fog or ice fog, in patches
    'Rūkas arba ledo rūkas, padidėjo per paskutinę valandą': 34,  # 34+ Fog, or ice fog, has increased in the last hour / Fog or ice fog, become thicker during the past hour
    'Nėra': 0,  # 00+ No precipitation/ Clear
    'Liūtis, silpna': 61,  # 61+ Rain, light / Rain, light
    'Lietus, silpnas': 61,  # 61+ Rain, light / Rain, light
    'Lietus, vidutinis': 62,  # 62+ Rain, medium / Rain, moderate
    'Lietus, stiprus': 63,  # 63+ Rain, heavy / Rain, heavy
    'Liūtis, vidutinė': 62,  # 62? Downpour moderate ?
    'Dulksna, silpna': 51,  # 51+ Drizzle, light / Drizzle, not freezing, slight
    'Dulksna, vidutinė': 52,  # 52+ Drizzle, medium / Drizzle, not freezing, moderate
    'Dulksna, stipri': 53,  # 53+ Drizzle, heavy' / Drizzle, not freezing, heavy
    'Dulksna ir lietus, silpnas': 61,  # 61 Mist and rain, weak / Rain, light
    'Migla': 5,  # 5+ Haze / Haze or smoke, or dust in suspension in the air, visibility < 1 km
    'Migla, dūmai arba dulkės, matomumas daugiau nei 1 km': 4,  # 4+ Fog, smoke or dust, visibility more than 1 km / Haze or smoke, or dust in suspension in the air, visibility ≥ 1 km
    'Nėra (p. pask. val. sniegas)': 24,  # ? Snygis / Snow
    'Snygis, silpnas': 71,  # + Snow, light
    'Snygis, vidutinis': 72, # + Snow, moderate
    'Snygis, stiprus': 73,  # + Snow, heavy
    'Šlapdriba, silpna': 67,  # Rain (or drizzle) and snow, light
    'Liūtis arba protarpiais krituliai': 41,  #  Precipitation, slight or moderate(raining now)
    # 'Snygis, liūtinis silpnas': Снег, проливной дождь легкий дословно. Нет соответствия.
}
