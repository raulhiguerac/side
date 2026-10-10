<template>
  <AdminSplitView :error="error">
    <template #filters>
      <AdminFilterBar
        :filters="MODERATION_FILTERS"
        :initial="urlFilters"
        :loading="loading"
        @apply="pushFilters"
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
      <AdminPaginationFooter
        :range="range"
        :total="serverTotal"
        :has-prev="hasPrev"
        :has-next="hasNext"
        @prev="prev"
        @next="next"
      />
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
import { nextTick, useTemplateRef, watch } from "vue";
import AdminPaginationFooter from "@/components/admin/shared/AdminPaginationFooter.vue";
import AdminSplitView from "@/components/admin/shared/AdminSplitView.vue";
import AdminFilterBar from "@/components/admin/shared/AdminFilterBar.vue";
import AdminPropertiesTable from "@/components/admin/properties/AdminPropertiesTable.vue";
import AdminPropertyPreviewPanel from "@/components/admin/properties/AdminPropertyPreviewPanel.vue";
import AdminModerationForm from "@/components/admin/properties/moderation/AdminModerationForm.vue";
import { useAdminProperties } from "@/composables/admin/useAdminProperties";
import { useModerateProperty } from "@/composables/admin/useModerateProperty";
import { useRowSelection } from "@/composables/admin/useRowSelection";
import { useUrlFilters } from "@/composables/admin/useUrlFilters";
import { MODERATION_FILTERS } from "@/constants/propertiesFilters";
import type { ModerationPayload } from "@/types/admin/moderation";
import type { AdminPropertiesFilters } from "@/types/admin/properties";

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

// Acá y no en el panel: moderar también recarga la lista.
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
  if (!(await moderate(propertyId, payload))) return; // true aun con fallo parcial

  await reload();

  // Si la selección cambió, el panel ya recarga solo.
  const previousId = selectedId.value;
  await nextTick();
  if (selectedId.value === previousId) previewPanel.value?.refresh();
}

watch(selectedId, resetModeration); // los mensajes son de la fila anterior

const { urlFilters, pushFilters } = useUrlFilters<AdminPropertiesFilters>(
  MODERATION_FILTERS,
  load
);
</script>
