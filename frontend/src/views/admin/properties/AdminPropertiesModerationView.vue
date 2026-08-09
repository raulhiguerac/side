<template>
  <div class="flex items-start gap-6">
    <!-- `flex-[3]`/`flex-[2]` reparten después del gap; `min-w-0` deja que la tabla se encoja. -->
    <div class="min-w-0 flex-[3]">
      <p
        v-if="error"
        class="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600"
      >
        {{ error }}
      </p>

      <div class="rounded-2xl border border-brand-divider bg-white">
        <AdminPropertiesTable
          :rows="rows"
          :loading="loading"
          :selected-id="selectedId"
          @row-click="selectedId = $event.id"
        />
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

    <!-- Oculto bajo xl: moderar es una tarea de escritorio. -->
    <aside class="sticky top-6 hidden min-w-0 flex-[2] xl:block">
      <AdminPropertyPreviewPanel :property-id="selectedId" />
    </aside>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, ref, watch } from "vue";
import PaginationArrows from "@/components/shared/PaginationArrows.vue";
import AdminPropertiesTable from "@/components/admin/properties/AdminPropertiesTable.vue";
import AdminPropertyPreviewPanel from "@/components/admin/properties/AdminPropertyPreviewPanel.vue";
import { useAdminProperties } from "@/composables/admin/useAdminProperties";

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

const selectedId = ref<string | null>(null);

/** Arranca con la primera fila elegida; al paginar la anterior deja de estar visible. */
watch(
  rows,
  (list) => {
    if (!list.length) {
      selectedId.value = null;
      return;
    }
    if (!list.some((row) => row.id === selectedId.value)) {
      selectedId.value = list[0].id;
    }
  },
  { immediate: true }
);

onMounted(load);
</script>
