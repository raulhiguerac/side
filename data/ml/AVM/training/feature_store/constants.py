from __future__ import annotations

BOGOTA_LANDMARKS: dict[str, dict[str, float]] = {
    "andino":               {"lat": 4.6671,   "lon": -74.0538},
    "gran_estacion":        {"lat": 4.6489,   "lon": -74.1013},
    "titan_plaza":          {"lat": 4.695028, "lon": -74.086222},
    "portal_norte_tm":      {"lat": 4.7540,   "lon": -74.0468},
    "portal_sur_tm":        {"lat": 4.5722,   "lon": -74.1665},
    "portal_80_tm":         {"lat": 4.7095,   "lon": -74.1107},
    "universidad_andes":    {"lat": 4.6011,   "lon": -74.0661},
    "universidad_nacional": {"lat": 4.6383,   "lon": -74.0841},
    "centro_internacional": {"lat": 4.612611, "lon": -74.070500},
    "parque_simon_bolivar": {"lat": 4.6584,   "lon": -74.0937},
    "parque_virrey":        {"lat": 4.6769,   "lon": -74.0565},
    "aeropuerto_eldorado":  {"lat": 4.7016,   "lon": -74.1469},
}

ANTIGUEDAD_BINS: list[float]  = [0, 1, 9, 16, 31, float('inf')]
ANTIGUEDAD_LABELS: list[str]  = ['menor a 1 año', '1 a 8 años', '9 a 15 años', '16 a 30 años', 'más de 30 años']

PROPERTY_TYPE_MAP: dict[str, int] = {'apartment': 0, 'house': 1}

RENAME_MAP: dict[str, str] = {
    'bedrooms':      'cuartos',
    'bathrooms':     'banios',
    'parking_spots': 'parqueaderos',
    'stratum':       'estrato',
    'property_type': 'tipo_propiedad',
}

H3_RESOLUTIONS: list[int] = [6, 7, 8]

POI_RADII_KM: list[float] = [0.3, 0.8, 1.2]

AMENITY_MAP: dict[str, list[str]] = {
    'transport':  ['bus_station', 'taxi', 'bicycle_parking', 'bicycle_rental', 'parking'],
    'food':       ['restaurant', 'cafe', 'fast_food', 'bar', 'pub', 'food_court', 'juice_bar', 'ice_cream'],
    'education':  ['school', 'college', 'university', 'kindergarten', 'language_school', 'music_school', 'driving_school'],
    'health':     ['hospital', 'clinic', 'pharmacy', 'doctors', 'dentist', 'veterinary'],
    'finance':    ['bank', 'atm', 'bureau_de_change', 'money_transfer'],
    'commerce':   ['marketplace', 'fuel', 'car_wash', 'car_rental'],
    'recreation': ['cinema', 'theatre', 'arts_centre', 'library', 'community_centre', 'nightclub', 'casino', 'concert_hall', 'events_venue'],
    'worship':    ['place_of_worship'],
    'adult':      ['stripclub', 'brothel', 'swingerclub', 'love_hotel'],
}

SHOP_MAP: dict[str, list[str]] = {
    'food':        ['supermarket', 'convenience', 'bakery', 'butcher', 'greengrocer', 'grocery',
                    'seafood', 'dairy', 'deli', 'frozen_food', 'health_food', 'pasta', 'farm',
                    'tea', 'ice_cream', 'cake', 'pastry', 'chocolate', 'confectionery', 'coffee',
                    'beverages', 'alcohol', 'wine', 'kiosk', 'bodega'],
    'commerce':    ['mall', 'department_store', 'variety_store', 'general', 'wholesale', 'second_hand'],
    'fashion':     ['clothes', 'shoes', 'bag', 'fashion', 'fashion_accessories', 'boutique',
                    'jewelry', 'watches', 'leather', 'tailor', 'fabric', 'cosmetics', 'perfumery',
                    'beauty', 'hairdresser', 'optician', 'tattoo'],
    'home':        ['furniture', 'hardware', 'doityourself', 'household', 'houseware',
                    'interior_decoration', 'kitchen', 'bathroom_furnishing', 'bed', 'carpet',
                    'flooring', 'tiles', 'paint', 'lighting', 'curtain', 'window_blind', 'appliance'],
    'electronics': ['electronics', 'computer', 'mobile_phone', 'hifi', 'radiotechnics', 'electrical'],
    'health':      ['chemist', 'medical_supply', 'massage', 'nutrition_supplements', 'hearing_aids'],
    'auto':        ['car', 'car_repair', 'car_parts', 'motorcycle', 'motorcycle_repair', 'motorcycle_parts', 'tyres', 'bicycle'],
    'services':    ['laundry', 'dry_cleaning', 'copyshop', 'printing', 'travel_agency',
                    'storage_rental', 'locksmith', 'shoe_repair', 'repair', 'telecommunication'],
    'leisure':     ['sports', 'outdoor', 'music', 'musical_instrument', 'video_games', 'video',
                    'toys', 'hobby', 'fishing', 'golf', 'books', 'stationery', 'art', 'gift',
                    'photo', 'florist', 'pet', 'pet_grooming'],
    'adult':       ['erotic', 'cannabis', 'tobacco', 'cigars'],
}

PUBLIC_TRANSPORT_MAP: dict[str, list[str]] = {
    'transport': ['stop_position', 'platform', 'station', 'platform;stop_position'],
}

LEISURE_MAP: dict[str, list[str]] = {
    'recreation': ['park', 'garden', 'nature_reserve', 'playground', 'dog_park',
                   'sports_centre', 'fitness_centre', 'fitness_station', 'pitch',
                   'stadium', 'sports_hall', 'recreation_ground', 'swimming_pool',
                   'swimming_area', 'golf_course', 'miniature_golf', 'bowling_alley',
                   'horse_riding', 'dance', 'amusement_arcade', 'indoor_play',
                   'escape_game', 'sauna', 'spa', 'club'],
}

HEALTHCARE_MAP: dict[str, list[str]] = {
    'health': ['hospital', 'clinic', 'doctor', 'pharmacy', 'dentist', 'rehabilitation',
               'physiotherapist', 'nurse', 'audiologist', 'optometrist', 'speech_therapist',
               'podiatrist', 'radiology', 'laboratory', 'blood_donation'],
}

