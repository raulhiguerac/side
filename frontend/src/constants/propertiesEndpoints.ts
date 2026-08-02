export const PROPERTIES_ENDPOINTS = {
  me: "/v1/properties/me",
  byId: (id: string) => `/v1/properties/${id}`,
  byUser: (userId: string) => `/v1/properties/users/${userId}`,
  visibility: (id: string) => `/v1/properties/${id}/visibility`,
  images: (id: string) => `/v1/properties/${id}/images`,
  adminList: "/v1/admin/properties",
  /**
   * No sirve el detalle público: `GetPropertyUseCase` tira 404 si el listing no
   * está `active` y no sos el dueño, o sea justo los borradores e inactivos que
   * hay que moderar.
   */
  adminDetail: (id: string) => `/v1/admin/properties/${id}`,
};
