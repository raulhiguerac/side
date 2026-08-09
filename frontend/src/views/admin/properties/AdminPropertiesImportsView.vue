<template>
  <div>
    <div class="mb-6 flex justify-end">
      <button
        @click="isBulkModalOpen = true"
        class="flex items-center gap-2 whitespace-nowrap rounded-xl bg-brand-primary px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90"
      >
        <Upload class="w-4 h-4" />
        Importar CSV
      </button>
    </div>

    <!-- Empty state fijo: el backend no lista jobs, solo el status de uno por id. -->
    <div
      class="rounded-2xl border border-brand-divider bg-white px-6 py-12 text-center"
    >
      <p class="text-brand-text text-sm font-medium">Sin importaciones</p>
      <p class="text-brand-muted mt-1 text-sm">
        El historial de importaciones todavía no está disponible.
      </p>
    </div>

    <BulkUploadPropertiesModal v-model="isBulkModalOpen" />
  </div>
</template>

<script lang="ts" setup>
import { ref } from "vue";
import { Upload } from "@lucide/vue";
import BulkUploadPropertiesModal from "@/components/admin/properties/BulkUploadPropertiesModal.vue";

const isBulkModalOpen = ref(false);
</script>
