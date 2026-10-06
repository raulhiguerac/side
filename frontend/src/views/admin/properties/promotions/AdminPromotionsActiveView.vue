<template>
  <AdminSplitView :error="error">
    <template #table>
      <AdminPromotionsTable
        :rows="promotions"
        :loading="loading"
        :selected-id="selectedId"
        @row-click="selectedId = $event.property_id"
      />
    </template>

    <template #footer>
      <div
        v-if="total"
        class="mt-6 flex flex-col items-center gap-3 sm:flex-row sm:justify-between"
      >
        <p class="text-brand-muted text-sm">
          Mostrando {{ range.from }}-{{ range.to }} de
          {{ total.toLocaleString("es-CO") }}
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
        <!-- El pie es un botón: lo que hay que saber de la promoción ya está en la fila. -->
        <template #footer="{ property }">
          <div
            class="border-brand-divider sticky bottom-0 border-t bg-white px-5 py-4"
          >
            <h3
              class="text-brand-muted mb-3 text-xs font-semibold tracking-wide uppercase"
            >
              Promoción
            </h3>

            <p
              v-if="removeError"
              class="mb-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600"
            >
              {{ removeError }}
            </p>

            <div class="flex justify-end">
              <button
                type="button"
                class="rounded-xl border border-red-200 px-4 py-2 text-sm font-semibold text-red-600 transition-colors hover:bg-red-50"
                @click="pendingRemovalId = property.id"
              >
                Quitar
              </button>
            </div>
          </div>
        </template>
      </AdminPropertyPreviewPanel>
    </template>
  </AdminSplitView>

  <RemovePromotionModal
    :property-id="pendingRemovalId"
    :removing="removing"
    @close="pendingRemovalId = null"
    @confirm="onRemove"
  />
</template>

<script lang="ts" setup>
import { onMounted, ref, watch } from "vue";
import PaginationArrows from "@/components/shared/PaginationArrows.vue";
import AdminSplitView from "@/components/admin/shared/AdminSplitView.vue";
import AdminPromotionsTable from "@/components/admin/properties/promotions/AdminPromotionsTable.vue";
import AdminPropertyPreviewPanel from "@/components/admin/properties/AdminPropertyPreviewPanel.vue";
import RemovePromotionModal from "@/components/admin/properties/promotions/RemovePromotionModal.vue";
import { useActivePromotions } from "@/composables/admin/useActivePromotions";
import { useRowSelection } from "@/composables/admin/useRowSelection";

const {
  promotions,
  total,
  range,
  hasPrev,
  hasNext,
  loading,
  error,
  removing,
  removeError,
  load,
  reload,
  remove,
  next,
  prev,
} = useActivePromotions();

/** Se selecciona por `property_id`: la fila es una promoción, pero el panel muestra la property. */
const { selectedId } = useRowSelection(promotions, (row) => row.property_id);

/** El modal se abre con el id a borrar, no con un booleano: sin id no hay nada que confirmar. */
const pendingRemovalId = ref<string | null>(null);

/**
 * El modal se cierra pase lo que pase y el error se muestra en el pie del panel,
 * que es donde el admin queda mirando. Al recargar, la property que dejó de
 * estar promocionada ya no vuelve en el listado.
 */
async function onRemove() {
  if (!pendingRemovalId.value) return;

  const ok = await remove(pendingRemovalId.value);
  pendingRemovalId.value = null;
  if (ok) await reload();
}

/** El error es de la property que se intentó quitar: cambiar de fila lo invalida. */
watch(selectedId, () => {
  removeError.value = null;
});

onMounted(() => load(1));
</script>
