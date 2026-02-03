<template>
  <aside class="w-56 h-fit">
    <!-- Header del sidebar -->
    <div class="mb-4">
      <h2 class="text-brand-text text-lg font-bold">Configuración</h2>
      <p class="text-brand-muted text-sm mt-1">Gestiona tu cuenta</p>
    </div>

    <!-- Navigation -->
    <nav>
      <ul class="space-y-1">
        <li v-for="item in menuItems" :key="item.path">
          <router-link
            :to="item.path"
            class="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all"
            :class="
              isActive(item.path)
                ? 'bg-brand-primary text-white'
                : 'text-brand-text hover:bg-white'
            "
          >
            <component :is="item.icon" class="w-5 h-5" />
            {{ item.label }}
          </router-link>
        </li>
      </ul>
    </nav>
  </aside>
</template>

<script lang="ts" setup>
import { useRoute } from "vue-router";
import { h } from "vue";

const route = useRoute();

// Iconos como componentes funcionales
const UserIcon = () =>
  h(
    "svg",
    {
      xmlns: "http://www.w3.org/2000/svg",
      width: "20",
      height: "20",
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      "stroke-width": "2",
      "stroke-linecap": "round",
      "stroke-linejoin": "round",
    },
    [
      h("circle", { cx: "12", cy: "8", r: "5" }),
      h("path", { d: "M20 21a8 8 0 0 0-16 0" }),
    ]
  );

const ShieldIcon = () =>
  h(
    "svg",
    {
      xmlns: "http://www.w3.org/2000/svg",
      width: "20",
      height: "20",
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      "stroke-width": "2",
      "stroke-linecap": "round",
      "stroke-linejoin": "round",
    },
    [
      h("path", {
        d: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
      }),
    ]
  );

const AlertIcon = () =>
  h(
    "svg",
    {
      xmlns: "http://www.w3.org/2000/svg",
      width: "20",
      height: "20",
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      "stroke-width": "2",
      "stroke-linecap": "round",
      "stroke-linejoin": "round",
    },
    [
      h("circle", { cx: "12", cy: "12", r: "10" }),
      h("line", { x1: "12", x2: "12", y1: "8", y2: "12" }),
      h("line", { x1: "12", x2: "12.01", y1: "16", y2: "16" }),
    ]
  );

const menuItems = [
  { path: "/settings/profile", label: "Mi Perfil", icon: UserIcon },
  { path: "/settings/security", label: "Seguridad", icon: ShieldIcon },
  { path: "/settings/account", label: "Cuenta", icon: AlertIcon },
];

const isActive = (path: string) => route.path === path;
</script>
