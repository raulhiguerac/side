export const PROPERTIES_ENDPOINTS = {
  me: "/v1/properties/me",
  byId: (id: string) => `/v1/properties/${id}`,
  byUser: (userId: string) => `/v1/properties/users/${userId}`,
  visibility: (id: string) => `/v1/properties/${id}/visibility`,
  images: (id: string) => `/v1/properties/${id}/images`,
  adminList: "/v1/admin/properties",
  /** El detalle público tira 404 en borradores e inactivos, o sea justo lo que hay que moderar. */
  adminDetail: (id: string) => `/v1/admin/properties/${id}`,
  /** Ejes independientes y ambos `204`: mover los dos son dos PATCH sin respuesta útil. */
  adminVerification: (id: string) => `/v1/admin/properties/${id}/verification`,
  adminStatus: (id: string) => `/v1/admin/properties/${id}/status`,
  /** GET lista las promocionadas (como `PropertyCardSchema`, no como promociones); POST crea una. */
  adminPromotions: "/v1/admin/promotions",
  /** GET las de una property; DELETE baja la activa — el path va por property, no por id de promoción. */
  adminPropertyPromotions: (id: string) =>
    `/v1/admin/properties/${id}/promotions`,
};
