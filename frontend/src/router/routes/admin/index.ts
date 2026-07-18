import type { RouteRecordRaw } from "vue-router";
import { adminHomeRoutes } from "./home";
import { adminPropertiesRoutes } from "./properties";
import { adminCatalogRoutes } from "./catalog";

export const adminRoutes: RouteRecordRaw[] = [
  ...adminHomeRoutes,
  ...adminPropertiesRoutes,
  ...adminCatalogRoutes,
];
