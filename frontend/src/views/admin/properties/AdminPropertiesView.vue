<template>
  <PageContainer>
    <div class="py-8">
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1
            class="text-brand-text text-2xl font-bold flex items-center gap-2"
          >
            <Home class="w-6 h-6 text-brand-primary" />
            Admin — Propiedades
          </h1>
          <p class="text-brand-muted text-sm mt-1">
            Moderación, precios estimados, promociones y carga masiva.
          </p>
        </div>
        <button
          @click="isBulkModalOpen = true"
          class="px-4 py-2 rounded-xl bg-brand-primary text-white text-sm font-medium hover:opacity-90 transition-opacity whitespace-nowrap flex items-center gap-2"
        >
          <Upload class="w-4 h-4" />
          Importar CSV
        </button>
      </div>

      <p
        v-if="error"
        class="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600"
      >
        {{ error }}
      </p>

      <div class="rounded-2xl border border-brand-divider bg-white">
        <AdminPropertiesTable :rows="rows" :loading="loading" />
      </div>

      <div
        v-if="serverTotal"
        class="mt-6 flex flex-col items-center gap-3 sm:flex-row sm:justify-between"
      >
        <p class="text-brand-muted text-sm">
          Mostrando {{ range.from }}-{{ range.to }} de
          {{ serverTotal.toLocaleString("es-CO") }}
        </p>
        <PaginationArrows
          :has-prev="hasPrev"
          :has-next="hasNext"
          @prev="prev"
          @next="next"
        />
      </div>
    </div>

    <BulkUploadPropertiesModal v-model="isBulkModalOpen" />
  </PageContainer>
</template>

<script lang="ts" setup>
import { ref, onMounted } from "vue";
import { Home, Upload } from "@lucide/vue";
import PageContainer from "@/components/shared/PageContainer.vue";
import PaginationArrows from "@/components/shared/PaginationArrows.vue";
import BulkUploadPropertiesModal from "@/components/admin/properties/BulkUploadPropertiesModal.vue";
import AdminPropertiesTable from "@/components/admin/properties/AdminPropertiesTable.vue";
import { useAdminProperties } from "@/composables/admin/useAdminProperties";

const isBulkModalOpen = ref(false);

const {
  rows,
  hasPrev,
  hasNext,
  serverTotal,
  range,
  loading,
  error,
  load,
  next,
  prev,
} = useAdminProperties();

onMounted(load);
</script>
