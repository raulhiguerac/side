import type { RouteRecordRaw } from "vue-router";

export const propertiesRoutes: RouteRecordRaw[] = [
  {
    path: "/properties",
    name: "my-properties",
    component: () =>
      import("@/views/properties/dashboard/MyPropertiesView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/properties/create",
    name: "create-property",
    component: () => import("@/views/properties/create/CreatePropertyView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/properties/:id/edit",
    name: "edit-property",
    component: () => import("@/views/properties/edit/EditPropertyView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/listing/:id",
    name: "property-detail",
    component: () => import("@/views/properties/detail/PropertyDetailView.vue"),
    meta: { requiresAuth: false },
  },
  {
    path: "/feed",
    component: () => import("@/views/properties/feed/PropertiesView.vue"),
    meta: { requiresAuth: false },
    children: [
      { path: "", redirect: "/feed/list" },
      {
        path: "list",
        name: "feed-list",
        component: () => import("@/views/properties/feed/FeedView.vue"),
      },
      {
        path: "map",
        name: "feed-map",
        component: () => import("@/views/properties/feed/MapView.vue"),
      },
    ],
  },
];
