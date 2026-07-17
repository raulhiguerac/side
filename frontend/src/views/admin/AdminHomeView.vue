<template>
  <PageContainer>
    <div class="py-8">
      <!-- Hero -->
      <div class="mb-8">
        <h1 class="text-brand-text text-2xl font-bold">Sección Admin</h1>
        <p class="text-brand-muted text-sm mt-1">
          Panel de moderación y gestión del catálogo.
        </p>
      </div>

      <!-- KPIs -->
      <h2
        class="text-brand-muted text-xs font-semibold uppercase tracking-wide mb-3"
      >
        KPIs
      </h2>
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        <div
          v-for="metric in metrics"
          :key="metric.label"
          class="bg-white rounded-2xl border border-brand-divider p-6"
        >
          <p class="text-brand-muted text-sm">{{ metric.label }}</p>
          <p class="text-brand-text text-2xl font-bold mt-1">
            {{ metric.value }}
          </p>
        </div>
      </div>

      <hr class="border-brand-divider mb-10" />

      <!-- Gestión -->
      <h2
        class="text-brand-muted text-xs font-semibold uppercase tracking-wide mb-3"
      >
        Gestión
      </h2>
      <div class="grid sm:grid-cols-2 gap-4">
        <div class="bg-white rounded-2xl border border-brand-divider p-6 md:p-8">
          <h3 class="text-brand-text text-lg font-semibold flex items-center gap-2">
            <Home class="w-5 h-5 text-brand-primary" />
            Propiedades
          </h3>
          <p class="text-brand-muted text-sm mt-1">
            Moderación, precios estimados, promociones y carga masiva.
          </p>
          <router-link
            to="/admin/properties"
            class="inline-block mt-4 px-4 py-2 rounded-xl bg-brand-primary text-white text-sm font-medium hover:opacity-90 transition-opacity"
          >
            Administrar propiedades
          </router-link>
        </div>

        <div class="bg-white rounded-2xl border border-brand-divider p-6 md:p-8">
          <h3 class="text-brand-text text-lg font-semibold flex items-center gap-2">
            <Globe class="w-5 h-5 text-brand-primary" />
            Catálogo
          </h3>
          <p class="text-brand-muted text-sm mt-1">
            Países, localidades, barrios y enriquecimiento de geometría.
          </p>
          <router-link
            to="/admin/catalog"
            class="inline-block mt-4 px-4 py-2 rounded-xl bg-brand-primary text-white text-sm font-medium hover:opacity-90 transition-opacity"
          >
            Administrar catálogo
          </router-link>
        </div>
      </div>
    </div>
  </PageContainer>
</template>

<script lang="ts" setup>
import { Home, Globe } from "@lucide/vue";
import PageContainer from "@/components/shared/PageContainer.vue";

// Placeholder — wiring a endpoints reales de conteo queda pendiente (users-service/properties-service/catalog-service)
const metrics = [
  { label: "Usuarios", value: "—" },
  { label: "Propiedades", value: "—" },
  { label: "Localidades", value: "—" },
  { label: "Barrios", value: "—" },
];
</script>
