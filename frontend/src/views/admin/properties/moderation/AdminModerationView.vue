<template>
  <AdminSplitView :error="error">
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
import { nextTick, onMounted, useTemplateRef, watch } from "vue";
import PaginationArrows from "@/components/shared/PaginationArrows.vue";
import AdminSplitView from "@/components/admin/shared/AdminSplitView.vue";
import AdminPropertiesTable from "@/components/admin/properties/AdminPropertiesTable.vue";
import AdminPropertyPreviewPanel from "@/components/admin/properties/AdminPropertyPreviewPanel.vue";
import AdminModerationForm from "@/components/admin/properties/moderation/AdminModerationForm.vue";
import { useAdminProperties } from "@/composables/admin/useAdminProperties";
import { useModerateProperty } from "@/composables/admin/useModerateProperty";
import { useRowSelection } from "@/composables/admin/useRowSelection";
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

onMounted(load);
</script>
