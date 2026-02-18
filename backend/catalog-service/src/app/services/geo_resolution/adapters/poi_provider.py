import uuid
import unicodedata
from datetime import datetime, timezone

from app.services.geo_resolution.ports.poi_provider_gateway import PoiProviderGateway
from app.integrations.georef.pois.overpass import PoiClient
from app.models.location import PointOfInterest, PoiSource


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def _extract_category(props: dict) -> tuple[str | None, list[str] | None]:
    tags = ["amenity", "leisure", "shop"]
    found = [(tag, props[tag]) for tag in tags if tag in props]
    if not found:
        return None, None
    primary = found[0][1]
    subs = [v for _, v in found[1:]] if len(found) > 1 else None
    return primary, subs


def _build_address(props: dict) -> str | None:
    street = props.get("addr:street")
    number = props.get("addr:housenumber")
    if not street:
        return None
    return f"{street} {number}".strip() if number else street


class PoiProviderAdapter(PoiProviderGateway):

    def __init__(self, client: PoiClient):
        self.client = client

    async def get_pois_by_bbox(
        self,
        *,
        bbox: list[float],
        locality_id: uuid.UUID,
        neighborhood_id: uuid.UUID,
        h3_index: str,
    ) -> list[PointOfInterest]:
        geojson = await self.client.get_pois_by_bbox(bbox=bbox)
        now = datetime.now(timezone.utc)
        pois = []

        for feature in geojson.get("features", []):
            props = feature.get("properties", {})
            geom = feature.get("geometry", {})
            coords = geom.get("coordinates", [None, None])
            name = props.get("name")

            if not name or len(coords) < 2:
                continue

            lon, lat = coords[0], coords[1]
            category, subcategories = _extract_category(props)

            pois.append(PointOfInterest(
                locality_id=locality_id,
                neighborhood_id=neighborhood_id,
                external_id=props.get("@id"),
                source=PoiSource.osm,
                raw_response=feature,
                fetched_at=now,
                name=name,
                search_name=_normalize(name),
                full_address=_build_address(props),
                category=category,
                subcategories=subcategories,
                latitude=lat,
                longitude=lon,
                h3_index=h3_index,
                phone=props.get("phone"),
                website=props.get("website"),
            ))

        return pois
