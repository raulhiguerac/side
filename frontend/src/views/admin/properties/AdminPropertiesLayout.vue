<template>
  <PageContainer>
    <div class="py-8">
      <div class="mb-6">
        <h1 class="text-brand-text text-2xl font-bold flex items-center gap-2">
          <Home class="w-6 h-6 text-brand-primary" />
          Admin — Propiedades
        </h1>
        <p class="text-brand-muted text-sm mt-1">
          Moderación, precios estimados, promociones y carga masiva.
        </p>
      </div>

      <!--
        `flex-1` en cada tab reparte el ancho en tres partes iguales; el
        `-mb-px` sube el borde activo un pixel para que tape la línea divisoria
        en vez de dibujarse debajo de ella.

        `custom` + `<a>` en vez de dejar que RouterLink renderice: hace falta
        el `v-slot` para leer `isExactActive` y aplicar el ternario. Con las
        props `active-class`/`exact-active-class` las dos variantes conviven en
        el atributo y gana la que Tailwind haya emitido última en el CSS, no la
        que corresponde.

        Exact y no `isActive`: `/admin/properties` es prefijo de las otras dos,
        así que con activo por prefijo "Moderación" quedaría encendida también
        al estar parado en promociones o importaciones.
      -->
      <nav class="flex border-b border-brand-divider">
        <RouterLink
          v-for="tab in TABS"
          :key="tab.to"
          :to="tab.to"
          custom
          v-slot="{ href, navigate, isExactActive }"
        >
          <a
            :href="href"
            @click="navigate"
            class="flex-1 -mb-px border-b-2 pb-3 text-center text-sm font-medium transition-colors"
            :class="
              isExactActive
                ? 'border-brand-primary text-brand-primary'
                : 'border-transparent text-brand-muted hover:text-brand-text'
            "
          >
            {{ tab.label }}
          </a>
        </RouterLink>
      </nav>

      <div class="mt-6">
        <RouterView />
      </div>
    </div>
  </PageContainer>
</template>

<script lang="ts" setup>
import { RouterLink, RouterView } from "vue-router";
import { Home } from "@lucide/vue";
import PageContainer from "@/components/shared/PageContainer.vue";

const TABS = [
  { label: "Moderación", to: "/admin/properties" },
  { label: "Promociones", to: "/admin/properties/promotions" },
  { label: "Importaciones", to: "/admin/properties/imports" },
] as const;
</script>
