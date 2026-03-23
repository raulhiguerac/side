export const API = {
  USERS_BASE_URL: process.env.VUE_APP_USERS_URL ?? "http://localhost:8000",
  CATALOG_BASE_URL: process.env.VUE_APP_CATALOG_URL ?? "http://localhost:8001",
  IPAPI_URL: process.env.VUE_APP_IPAPI_URL ?? "https://ipapi.co/json/",
};

export const STORAGE_KEYS = {
  USER_LOCATION: "userLocation",
  COUNTRIES: "countries",
  CITIES_BY_COUNTRY: (id: string) => `cities:${id}`,
  NEIGHBORHOODS_BY_LOCALITY: (id: string) => `neighborhoods:${id}`,  // sessionStorage
  ONBOARDING_DISMISSED: "onboarding_dismissed",
};
