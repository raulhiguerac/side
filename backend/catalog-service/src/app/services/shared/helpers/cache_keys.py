import uuid


# ---------------------------------------------------------------------------
# Countries
# ---------------------------------------------------------------------------

def cache_key_country(*, country_id: uuid.UUID) -> str:
    return f"catalog:country:{country_id}"


# ---------------------------------------------------------------------------
# Admin divisions
# ---------------------------------------------------------------------------

def cache_key_admin_division(*, admin_division_id: uuid.UUID) -> str:
    return f"catalog:admin_division:{admin_division_id}"


# ---------------------------------------------------------------------------
# Localities
# ---------------------------------------------------------------------------

def cache_key_localities(*, country_id: uuid.UUID) -> str:
    return f"catalog:{country_id}:localities"


def cache_key_localities_by_admin_division(*, admin_division_id: uuid.UUID) -> str:
    return f"catalog:admin_division:{admin_division_id}:localities"


def cache_key_locality(*, locality_id: uuid.UUID) -> str:
    return f"catalog:locality:{locality_id}"


# ---------------------------------------------------------------------------
# Neighborhoods
# ---------------------------------------------------------------------------

def cache_key_neighborhoods(*, locality_id: uuid.UUID) -> str:
    return f"catalog:locality:{locality_id}:neighborhoods"


def cache_key_neighborhood(*, neighborhood_id: uuid.UUID) -> str:
    return f"catalog:neighborhood:{neighborhood_id}"


# ---------------------------------------------------------------------------
# POIs
# ---------------------------------------------------------------------------

def cache_key_poi(*, poi_id: uuid.UUID) -> str:
    return f"catalog:poi:{poi_id}"


def cache_key_pois_by_locality(*, locality_id: uuid.UUID) -> str:
    return f"catalog:locality:{locality_id}:pois"


def cache_key_poi_by_external_id(*, external_id: str, source: str) -> str:
    return f"catalog:poi:{source}:{external_id}"
