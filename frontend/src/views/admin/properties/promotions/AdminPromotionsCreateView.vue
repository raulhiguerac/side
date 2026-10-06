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
      <AdminPropertyPreviewPanel :property-id="selectedId">
        <template #footer="{ property }">
          <AdminPromotionForm
            :property-id="property.id"
            :saving="saving"
            :success-message="success"
            :error-message="promotionError"
            @submit="onPromote($event, property.id)"
          />
        </template>
      </AdminPropertyPreviewPanel>
    </template>
  </AdminSplitView>
</template>

<script lang="ts" setup>
import { onMounted, watch } from "vue";
import AdminPaginationFooter from "@/components/admin/shared/AdminPaginationFooter.vue";
import AdminSplitView from "@/components/admin/shared/AdminSplitView.vue";
import AdminPropertiesTable from "@/components/admin/properties/AdminPropertiesTable.vue";
import AdminPropertyPreviewPanel from "@/components/admin/properties/AdminPropertyPreviewPanel.vue";
import AdminPromotionForm from "@/components/admin/properties/promotions/AdminPromotionForm.vue";
import { useAdminProperties } from "@/composables/admin/useAdminProperties";
import { usePromoteProperty } from "@/composables/admin/usePromoteProperty";
import { useRowSelection } from "@/composables/admin/useRowSelection";
import type { PromotionPayload } from "@/types/admin/promotions";

// Las elegibles son el listado de moderación: reusa composable y tabla.
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

const {
  saving,
  error: promotionError,
  success,
  promote,
  reset: resetPromotion,
} = usePromoteProperty();

const { selectedId } = useRowSelection(rows);

// Promocionar no cambia el detalle: solo se recarga la lista.
async function onPromote(payload: PromotionPayload, propertyId: string) {
  if (await promote(propertyId, payload)) await reload();
}

/** Los mensajes son de la property promocionada: cambiar de fila los invalida. */
watch(selectedId, resetPromotion);

// Mismas reglas que CreatePromotionUseCase: solo activas y sin promoción.
onMounted(() => load({ status: "active", is_promoted: false }));
</script>
