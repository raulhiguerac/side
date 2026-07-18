import unicodedata
import uuid
from datetime import datetime, timezone

from app.integrations.georef.pois.category_map import extract_category
from app.integrations.georef.pois.overpass import PoiClient
from app.models.location import PointOfInterest, PoiSource
from app.services.geo_resolution.ports.poi.gateway import PoiProviderGateway


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


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

        for element in geojson.get("elements", []):
            tags = element.get("tags", {})
            name = tags.get("name")
            if not name:
                continue

            if element["type"] == "node":
                lat = element.get("lat")
                lon = element.get("lon")
            else:
                center = element.get("center", {})
                lat = center.get("lat")
                lon = center.get("lon")

            if lat is None or lon is None:
                continue

            category = extract_category(tags)
            external_id = f"{element['type']}/{element['id']}"

            pois.append(PointOfInterest(
                locality_id=locality_id,
                neighborhood_id=neighborhood_id,
                external_id=external_id,
                source=PoiSource.osm,
                raw_response=element,
                fetched_at=now,
                name=name,
                search_name=_normalize(name),
                full_address=_build_address(tags),
                category=category,
                subcategories=None,
                latitude=lat,
                longitude=lon,
                h3_index=h3_index,
                phone=tags.get("phone"),
                website=tags.get("website"),
            ))

        return pois
