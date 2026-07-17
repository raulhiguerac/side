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

      <p class="text-brand-muted text-sm">En construcción.</p>
    </div>

    <BulkUploadPropertiesModal v-model="isBulkModalOpen" />
  </PageContainer>
</template>

<script lang="ts" setup>
import { ref } from "vue";
import { Home, Upload } from "@lucide/vue";
import PageContainer from "@/components/shared/PageContainer.vue";
import BulkUploadPropertiesModal from "@/components/admin/properties/BulkUploadPropertiesModal.vue";

const isBulkModalOpen = ref(false);
</script>
