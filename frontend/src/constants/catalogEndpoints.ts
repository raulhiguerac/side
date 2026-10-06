export const CATALOG_ENDPOINTS = {
  countries: "/v1/countries",
  localitiesByCountry: "/v1/localities/by-country",
  adminNeighborhoods: "/v1/admin/neighborhoods",
  adminNeighborhood: (id: string) => `/v1/admin/neighborhoods/${id}`,
  adminNeighborhoodGeometries: "/v1/admin/neighborhoods/geometries",
};
