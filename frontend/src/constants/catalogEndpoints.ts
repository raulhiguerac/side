export const CATALOG_ENDPOINTS = {
  countries: "/v1/countries",
  localitiesByCountry: "/v1/localities/by-country",
  neighborhoodsByLocalities: "/v1/neighborhoods/by-localities",
  neighborhoodById: "/v1/neighborhoods/by-id",
  resolveByCoordinates: "/v1/geo-resolution/by-coordinates",
  reachablePois: "/v1/geo-resolution/reachable-pois",
  adminAdminDivisions: "/v1/admin/admin-divisions",
  adminAdminDivision: (id: string) => `/v1/admin/admin-divisions/${id}`,
  adminCountries: "/v1/admin/countries",
  adminCountry: (id: string) => `/v1/admin/countries/${id}`,
  adminLocalities: "/v1/admin/localities",
  adminLocality: (id: string) => `/v1/admin/localities/${id}`,
  adminNeighborhoods: "/v1/admin/neighborhoods",
  adminNeighborhood: (id: string) => `/v1/admin/neighborhoods/${id}`,
  adminNeighborhoodGeometries: "/v1/admin/neighborhoods/geometries",
  adminNeighborhoodGeometry: (id: string) =>
    `/v1/admin/neighborhoods/${id}/geometry`,
  adminBulkNeighborhoods: (localityId: string) =>
    `/v1/admin/localities/${localityId}/neighborhoods/bulk`,
  adminBulkNeighborhoodGeometries: (localityId: string) =>
    `/v1/admin/localities/${localityId}/neighborhoods/bulk/geometry`,
};
