_AMENITY_MAP: dict[str, list[str]] = {
    "transport":  ["bus_station", "taxi", "bicycle_parking", "bicycle_rental", "parking"],
    "food":       ["restaurant", "cafe", "fast_food", "bar", "pub", "food_court", "juice_bar", "ice_cream"],
    "education":  ["school", "college", "university", "kindergarten", "language_school", "music_school", "driving_school"],
    "health":     ["hospital", "clinic", "pharmacy", "doctors", "dentist", "veterinary"],
    "finance":    ["bank", "atm", "bureau_de_change", "money_transfer"],
    "commerce":   ["marketplace", "fuel", "car_wash", "car_rental"],
    "recreation": ["cinema", "theatre", "arts_centre", "library", "community_centre", "nightclub", "casino", "concert_hall", "events_venue"],
    "worship":    ["place_of_worship"],
    "adult":      ["stripclub", "brothel", "swingerclub", "love_hotel"],
}

_SHOP_MAP: dict[str, list[str]] = {
    "food":        ["supermarket", "convenience", "bakery", "butcher", "greengrocer", "grocery",
                    "seafood", "dairy", "deli", "frozen_food", "health_food", "pasta", "farm",
                    "tea", "ice_cream", "cake", "pastry", "chocolate", "confectionery", "coffee",
                    "beverages", "alcohol", "wine", "kiosk", "bodega"],
    "commerce":    ["mall", "department_store", "variety_store", "general", "wholesale", "second_hand"],
    "fashion":     ["clothes", "shoes", "bag", "fashion", "fashion_accessories", "boutique",
                    "jewelry", "watches", "leather", "tailor", "fabric", "cosmetics", "perfumery",
                    "beauty", "hairdresser", "optician", "tattoo"],
    "home":        ["furniture", "hardware", "doityourself", "household", "houseware",
                    "interior_decoration", "kitchen", "bathroom_furnishing", "bed", "carpet",
                    "flooring", "tiles", "paint", "lighting", "curtain", "window_blind", "appliance"],
    "electronics": ["electronics", "computer", "mobile_phone", "hifi", "radiotechnics", "electrical"],
    "health":      ["chemist", "medical_supply", "massage", "nutrition_supplements", "hearing_aids"],
    "auto":        ["car", "car_repair", "car_parts", "motorcycle", "motorcycle_repair",
                    "motorcycle_parts", "tyres", "bicycle"],
    "services":    ["laundry", "dry_cleaning", "copyshop", "printing", "travel_agency",
                    "storage_rental", "locksmith", "shoe_repair", "repair", "telecommunication"],
    "leisure":     ["sports", "outdoor", "music", "musical_instrument", "video_games", "video",
                    "toys", "hobby", "fishing", "golf", "books", "stationery", "art", "gift",
                    "photo", "florist", "pet", "pet_grooming"],
    "adult":       ["erotic", "cannabis", "tobacco", "cigars"],
}

_PUBLIC_TRANSPORT_MAP: dict[str, list[str]] = {
    "transport": ["stop_position", "platform", "station"],
}

_LEISURE_MAP: dict[str, list[str]] = {
    "recreation": ["park", "garden", "nature_reserve", "playground", "dog_park",
                   "sports_centre", "fitness_centre", "fitness_station", "pitch",
                   "stadium", "sports_hall", "recreation_ground", "swimming_pool",
                   "swimming_area", "golf_course", "miniature_golf", "bowling_alley",
                   "horse_riding", "dance", "amusement_arcade", "indoor_play",
                   "escape_game", "sauna", "spa", "club"],
}

_HEALTHCARE_MAP: dict[str, list[str]] = {
    "health": ["hospital", "clinic", "doctor", "pharmacy", "dentist", "rehabilitation",
               "physiotherapist", "nurse", "audiologist", "optometrist", "speech_therapist",
               "podiatrist", "radiology", "laboratory", "blood_donation"],
}


def _build_lookup(m: dict[str, list[str]]) -> dict[str, str]:
    return {v: cat for cat, values in m.items() for v in values}


def _join_values(m: dict[str, list[str]]) -> str:
    return "|".join(v for values in m.values() for v in values)


# Overpass QL tag strings — one per OSM key
AMENITY_TAGS         = _join_values(_AMENITY_MAP)
SHOP_TAGS            = _join_values(_SHOP_MAP)
PUBLIC_TRANSPORT_TAGS = _join_values(_PUBLIC_TRANSPORT_MAP)
LEISURE_TAGS         = _join_values(_LEISURE_MAP)
HEALTHCARE_TAGS      = _join_values(_HEALTHCARE_MAP)

_AMENITY_LUT          = _build_lookup(_AMENITY_MAP)
_SHOP_LUT             = _build_lookup(_SHOP_MAP)
_PUBLIC_TRANSPORT_LUT = _build_lookup(_PUBLIC_TRANSPORT_MAP)
_LEISURE_LUT          = _build_lookup(_LEISURE_MAP)
_HEALTHCARE_LUT       = _build_lookup(_HEALTHCARE_MAP)


def extract_category(tags: dict[str, str | None]) -> str | None:
    return (
        _AMENITY_LUT.get(tags.get("amenity") or "")
        or _SHOP_LUT.get(tags.get("shop") or "")
        or _PUBLIC_TRANSPORT_LUT.get(tags.get("public_transport") or "")
        or _LEISURE_LUT.get(tags.get("leisure") or "")
        or _HEALTHCARE_LUT.get(tags.get("healthcare") or "")
    ) or None
