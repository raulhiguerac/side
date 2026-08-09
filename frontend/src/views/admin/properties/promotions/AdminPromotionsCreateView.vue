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
import PaginationArrows from "@/components/shared/PaginationArrows.vue";
import AdminSplitView from "@/components/admin/shared/AdminSplitView.vue";
import AdminPropertiesTable from "@/components/admin/properties/AdminPropertiesTable.vue";
import AdminPropertyPreviewPanel from "@/components/admin/properties/AdminPropertyPreviewPanel.vue";
import AdminPromotionForm from "@/components/admin/properties/promotions/AdminPromotionForm.vue";
import { useAdminProperties } from "@/composables/admin/useAdminProperties";
import { usePromoteProperty } from "@/composables/admin/usePromoteProperty";
import { useRowSelection } from "@/composables/admin/useRowSelection";
import type { PromotionPayload } from "@/types/admin";

/**
 * Las elegibles son el mismo listado admin de moderación, así que reusa su
 * composable y su tabla: lo único propio es el filtro.
 */
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

/**
 * Promocionar no cambia nada del detalle —`PropertyDetailSchema` no lleva
 * `is_promoted`— así que no hay panel que refrescar: solo la lista, de donde la
 * fila sale sola por dejar de cumplir `is_promoted: false`.
 */
async function onPromote(payload: PromotionPayload, propertyId: string) {
  if (await promote(propertyId, payload)) await reload();
}

/** Los mensajes son de la property promocionada: cambiar de fila los invalida. */
watch(selectedId, resetPromotion);

/**
 * Los dos filtros son las dos reglas que aplica `CreatePromotionUseCase`:
 * rechaza lo que no está `active` (`PropertyNotReadyForPromotionError`) y lo que
 * ya tiene promoción activa (`DuplicateActivePromotionError`). La lista muestra
 * exactamente lo que el backend va a aceptar, en vez de ofrecer y fallar.
 */
onMounted(() => load({ status: "active", is_promoted: false }));
</script>
