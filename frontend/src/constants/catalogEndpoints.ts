export const CATALOG_ENDPOINTS = {
  countries: "/v1/countries",
  localitiesByCountry: "/v1/localities/by-country",
  neighborhoodsByLocalities: "/v1/neighborhoods/by-localities",
  neighborhoodById: "/v1/neighborhoods/by-id",
  resolveByCoordinates: "/v1/geo-resolution/by-coordinates",
  reachablePois: "/v1/geo-resolution/reachable-pois",
  adminNeighborhoods: "/v1/admin/neighborhoods",
  adminNeighborhood: (id: string) => `/v1/admin/neighborhoods/${id}`,
  adminNeighborhoodGeometries: "/v1/admin/neighborhoods/geometries",
};
