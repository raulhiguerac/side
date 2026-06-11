import type { RouteRecordRaw } from "vue-router";

export const settingsRoutes: RouteRecordRaw[] = [
  {
    path: "/settings",
    component: () => import("@/views/settings/SettingsLayout.vue"),
    meta: { requiresAuth: true },
    children: [
      { path: "", redirect: "/settings/profile" },
      {
        path: "profile",
        name: "settings-profile",
        component: () => import("@/views/settings/SettingsProfile.vue"),
      },
      {
        path: "security",
        name: "settings-security",
        component: () => import("@/views/settings/SettingsSecurity.vue"),
      },
      {
        path: "account",
        name: "settings-account",
        component: () => import("@/views/settings/SettingsAccount.vue"),
      },
    ],
  },
];
