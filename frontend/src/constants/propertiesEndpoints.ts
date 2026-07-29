export const PROPERTIES_ENDPOINTS = {
  me: "/v1/properties/me",
  byId: (id: string) => `/v1/properties/${id}`,
  byUser: (userId: string) => `/v1/properties/users/${userId}`,
  visibility: (id: string) => `/v1/properties/${id}/visibility`,
  images: (id: string) => `/v1/properties/${id}/images`,
  adminList: "/v1/admin/properties",
};
