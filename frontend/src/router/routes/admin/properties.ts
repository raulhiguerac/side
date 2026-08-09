import type { RouteRecordRaw } from "vue-router";

/** El `name` vive en el hijo por defecto; el `meta` del padre alcanza porque el guard usa `matched`. */
export const adminPropertiesRoutes: RouteRecordRaw[] = [
  {
    path: "/admin/properties",
    component: () =>
      import("@/views/admin/properties/AdminPropertiesLayout.vue"),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: "",
        name: "admin-properties",
        component: () =>
          import("@/views/admin/properties/moderation/AdminModerationView.vue"),
      },
      {
        path: "promotions",
        component: () =>
          import(
            "@/views/admin/properties/promotions/AdminPromotionsLayout.vue"
          ),
        children: [
          {
            path: "",
            name: "admin-properties-promotions",
            component: () =>
              import(
                "@/views/admin/properties/promotions/AdminPromotionsActiveView.vue"
              ),
          },
          {
            path: "new",
            name: "admin-properties-promotions-new",
            component: () =>
              import(
                "@/views/admin/properties/promotions/AdminPromotionsCreateView.vue"
              ),
          },
        ],
      },
      {
        path: "imports",
        name: "admin-properties-imports",
        component: () =>
          import("@/views/admin/properties/imports/AdminImportsView.vue"),
      },
    ],
  },
];
