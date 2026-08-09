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
      <AdminPropertyPreviewPanel
        ref="previewPanel"
        :property-id="selectedId"
        :saving="saving"
        :success-message="success"
        :error-message="moderationError"
        @save="onSave"
      />
    </aside>
  </div>
</template>

<script lang="ts" setup>
import { nextTick, onMounted, ref, useTemplateRef, watch } from "vue";
import PaginationArrows from "@/components/shared/PaginationArrows.vue";
import AdminPropertiesTable from "@/components/admin/properties/AdminPropertiesTable.vue";
import AdminPropertyPreviewPanel from "@/components/admin/properties/AdminPropertyPreviewPanel.vue";
import { useAdminProperties } from "@/composables/admin/useAdminProperties";
import { useModerateProperty } from "@/composables/admin/useModerateProperty";
import type { ModerationPayload } from "@/types/admin";

const {
  rows,
  hasPrev,
  hasNext,
  serverTotal,
  range,
  loading,
  error,
  load,
  reload,
  next,
  prev,
} = useAdminProperties();

/** Moderar vive acá: lo que hay que refrescar después incluye la lista, que es de esta vista. */
const {
  saving,
  error: moderationError,
  success,
  moderate,
  reset: resetModeration,
} = useModerateProperty();

const previewPanel = useTemplateRef("previewPanel");

const selectedId = ref<string | null>(null);

async function onSave(payload: ModerationPayload, propertyId: string) {
  // Un fallo parcial también deja lo mostrado viejo, así que refresca igual.
  if (!(await moderate(propertyId, payload))) return;

  await reload();

  /** Si la selección se movió, el panel ya está cargando solo; el `nextTick` espera ese watcher. */
  const previousId = selectedId.value;
  await nextTick();
  if (selectedId.value === previousId) previewPanel.value?.refresh();
}

/** Los mensajes son de la property moderada: cambiar de fila los invalida. */
watch(selectedId, resetModeration);

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
