export const API = {
  USERS_BASE_URL: process.env.VUE_APP_USERS_URL ?? "/api/users",
  CATALOG_BASE_URL: process.env.VUE_APP_CATALOG_URL ?? "/api/catalog",
  AVM_BASE_URL: process.env.VUE_APP_AVM_URL ?? "/api/avm",
  PROPERTIES_BASE_URL: process.env.VUE_APP_PROPERTIES_URL ?? "/api/properties",
  IPAPI_URL: process.env.VUE_APP_IPAPI_URL ?? "https://ipapi.co/json/",
};

export const LIMITS = {
  MAX_IMAGES_PER_PROPERTY: 20,
};

export const STORAGE_KEYS = {
  USER_LOCATION: "userLocation",
  COUNTRIES: "countries",
  CITIES_BY_COUNTRY: (id: string) => `cities:${id}`,
  NEIGHBORHOODS_BY_LOCALITY: (id: string) => `neighborhoods:${id}`, // sessionStorage
  ONBOARDING_DISMISSED: (accountId: string) =>
    `onboarding_dismissed:${accountId}`, // sessionStorage
};
