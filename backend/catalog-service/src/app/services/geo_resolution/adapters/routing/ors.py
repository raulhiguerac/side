from app.integrations.georef.ors.routing import OrsRoutingClient
from app.services.geo_resolution.ports.routing.gateway import RoutingGateway

from app.services.geo_resolution.schemas.isochrone import IsochroneRequest, IsochroneEntry, GeoJsonPolygon


class OrsRoutingAdapter(RoutingGateway):
    def __init__(self, client: OrsRoutingClient):
        self.client = client

    async def get_isochrones(self, req: IsochroneRequest) -> list[IsochroneEntry]:
        geo_jsons = await self.client.get_isochrone(req=req)
        isochrones = []

        for feature in geo_jsons:
            if not feature.error:
                for feature_dict in feature.features:
                    isochrones.append(
                        IsochroneEntry(
                            profile=feature.profile,
                            range=feature_dict.get("properties", {}).get("value"),
                            isochrone=GeoJsonPolygon.model_validate(feature_dict["geometry"])
                        )
                    )
            else:
                isochrones.append(
                    IsochroneEntry(
                        profile=feature.profile,
                        range=None,
                        isochrone=None,
                    )
                )

        return isochrones
