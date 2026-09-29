import type { RouteRecordRaw } from "vue-router";

/** Igual que en propiedades: el `name` vive en el hijo por defecto y el `meta` del padre protege a todos. */
export const adminCatalogRoutes: RouteRecordRaw[] = [
  {
    path: "/admin/catalog",
    component: () => import("@/views/admin/catalog/AdminCatalogView.vue"),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: "",
        name: "admin-catalog",
        component: () =>
          import(
            "@/views/admin/catalog/neighborhoods/AdminNeighborhoodsView.vue"
          ),
      },
      {
        path: "localities",
        name: "admin-catalog-localities",
        component: () =>
          import("@/views/admin/catalog/localities/AdminLocalitiesView.vue"),
      },
      {
        path: "admin-divisions",
        name: "admin-catalog-admin-divisions",
        component: () =>
          import("@/views/admin/catalog/divisions/AdminDivisionsView.vue"),
      },
      {
        path: "countries",
        name: "admin-catalog-countries",
        component: () =>
          import("@/views/admin/catalog/countries/AdminCountriesView.vue"),
      },
    ],
  },
];
