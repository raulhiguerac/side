<template>
  <AdminSplitView :error="error">
    <template #filters>
      <AdminFilterBar
        :filters="MODERATION_FILTERS"
        :initial="urlFilters"
        :loading="loading"
        @apply="onApplyFilters"
      />
    </template>

    <template #table>
      <AdminPropertiesTable
        :rows="rows"
        :loading="loading"
        :selected-id="selectedId"
        @row-click="selectedId = $event.id"
      />
    </template>

    <template #footer>
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
    </template>

    <template #panel>
      <AdminPropertyPreviewPanel ref="previewPanel" :property-id="selectedId">
        <template #footer="{ property }">
          <AdminModerationForm
            :status="property.status"
            :verification-status="property.verification_status"
            :allowed-verification-targets="
              property.allowed_verification_targets
            "
            :allowed-status-targets="property.allowed_status_targets"
            :saving="saving"
            :success-message="success"
            :error-message="moderationError"
            @save="onSave($event, property.id)"
          />
        </template>
      </AdminPropertyPreviewPanel>
    </template>
  </AdminSplitView>
</template>

<script lang="ts" setup>
import { computed, nextTick, useTemplateRef, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import PaginationArrows from "@/components/shared/PaginationArrows.vue";
import AdminSplitView from "@/components/admin/shared/AdminSplitView.vue";
import AdminFilterBar from "@/components/admin/shared/AdminFilterBar.vue";
import AdminPropertiesTable from "@/components/admin/properties/AdminPropertiesTable.vue";
import AdminPropertyPreviewPanel from "@/components/admin/properties/AdminPropertyPreviewPanel.vue";
import AdminModerationForm from "@/components/admin/properties/moderation/AdminModerationForm.vue";
import { useAdminProperties } from "@/composables/admin/useAdminProperties";
import { useModerateProperty } from "@/composables/admin/useModerateProperty";
import { useRowSelection } from "@/composables/admin/useRowSelection";
import {
  LISTING_STATUS_LABELS,
  VERIFICATION_STATUS_LABELS,
} from "@/constants/propertyStatus";
import { sanitizeFilterQuery } from "@/utils/adminFilters";
import type {
  AdminFilterDefinition,
  AdminPropertiesFilters,
  ModerationPayload,
} from "@/types/admin";

/** Los dos filtros del listado admin que son enums; `owner_id` e `is_promoted` no
 * entran en un select. */
const MODERATION_FILTERS: readonly AdminFilterDefinition[] = [
  {
    key: "verification_status",
    label: "Verificación",
    options: VERIFICATION_STATUS_LABELS,
    allLabel: "Todas",
  },
  {
    key: "status",
    label: "Estado",
    options: LISTING_STATUS_LABELS,
    allLabel: "Todos",
  },
];

const route = useRoute();
const router = useRouter();

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

const { selectedId } = useRowSelection(rows);

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

/** La URL manda: así el filtro se comparte, se bookmarkea y el back del navegador
 * lo deshace. `page` sigue en memoria, que la paginación es incremental. */
const urlFilters = computed(() =>
  sanitizeFilterQuery(route.query, MODERATION_FILTERS)
);

function onApplyFilters(values: Record<string, string>) {
  // `push` y no `replace`: volver atrás devuelve el filtro anterior.
  router.push({ query: values });
}

// Los valores ya salieron saneados contra el enum, que es el mismo del backend.
watch(urlFilters, (filters) => load(filters as AdminPropertiesFilters), {
  immediate: true,
});
</script>
