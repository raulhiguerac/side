class ResolvePoiUseCase:
    """
    Cache-aside: DB local → Mapbox API → persist + return.

    Recibe query (texto) + locality context y resuelve POIs,
    priorizando cache local antes de llamar a Mapbox.
    """

    ...
