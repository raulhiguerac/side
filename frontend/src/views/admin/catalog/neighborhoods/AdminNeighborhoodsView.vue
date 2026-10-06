<template>
  <!-- Arriba del split y no en su slot: la cascada filtra la tabla y también el mapa. -->
  <AdminFilterBar
    class="mb-4"
    :filters="NEIGHBORHOOD_FILTERS"
    :initial="urlFilters"
    @apply="pushFilters"
  />

  <AdminSplitView :error="error">
    <template v-if="coverage" #filters>
      <NeighborhoodCoverageBar :coverage="coverage" />
    </template>

    <template #table>
      <AdminNeighborhoodsTable
        :rows="rows"
        :loading="loading"
        :selected-id="selectedId"
        @row-click="selectedId = $event.id"
      />
    </template>

    <template #panel>
      <AdminNeighborhoodPanel
        :neighborhood-id="selectedId"
        @action="activeAction = $event"
      />
    </template>

    <template #footer>
      <div
        v-if="totalItems"
        class="mt-6 flex flex-col items-center gap-3 sm:flex-row sm:justify-between"
      >
        <p class="text-brand-muted text-sm">
          Mostrando {{ range.from }}-{{ range.to }} de
          {{ totalItems.toLocaleString("es-CO") }}
        </p>
        <PaginationArrows
          :has-prev="hasPrev"
          :has-next="hasNext"
          @prev="prev"
          @next="next"
        />
      </div>
    </template>
  </AdminSplitView>

  <BaseModal
    :model-value="activeAction !== null"
    @update:model-value="activeAction = null"
  >
    <h3 class="text-brand-text mb-2 text-lg font-bold">
      {{ activeAction && MOCK_MODALS[activeAction] }}
    </h3>
    <p class="text-brand-muted mb-6 text-sm">Mock: contenido pendiente.</p>
    <button
      type="button"
      class="text-brand-text hover:bg-brand-bg w-full rounded-xl py-3 text-sm font-semibold transition-colors"
      @click="activeAction = null"
    >
      Cerrar
    </button>
  </BaseModal>
</template>

<script lang="ts" setup>
import { ref } from "vue";
import AdminNeighborhoodPanel from "@/components/admin/catalog/neighborhoods/AdminNeighborhoodPanel.vue";
import AdminNeighborhoodsTable from "@/components/admin/catalog/neighborhoods/AdminNeighborhoodsTable.vue";
import NeighborhoodCoverageBar from "@/components/admin/catalog/neighborhoods/NeighborhoodCoverageBar.vue";
import AdminFilterBar from "@/components/admin/shared/AdminFilterBar.vue";
import AdminSplitView from "@/components/admin/shared/AdminSplitView.vue";
import BaseModal from "@/components/shared/BaseModal.vue";
import PaginationArrows from "@/components/shared/PaginationArrows.vue";
import { useAdminNeighborhoods } from "@/composables/admin/useAdminNeighborhoods";
import { useRowSelection } from "@/composables/admin/useRowSelection";
import { useUrlFilters } from "@/composables/admin/useUrlFilters";
import { NEIGHBORHOOD_FILTERS } from "@/constants/catalogFilters";
import type { NeighborhoodAction } from "@/types/admin/catalog";

const {
  rows,
  totalItems,
  coverage,
  hasPrev,
  hasNext,
  range,
  loading,
  error,
  load,
  next,
  prev,
} = useAdminNeighborhoods();

const { selectedId } = useRowSelection(rows);

// Mock: título por acción hasta tener los modales reales.
const MOCK_MODALS: Record<NeighborhoodAction, string> = {
  edit: "Editar barrio",
  geometry: "Actualizar geometría",
  deactivate: "Desactivar barrio",
};

const activeAction = ref<NeighborhoodAction | null>(null);

const { urlFilters, pushFilters } = useUrlFilters(NEIGHBORHOOD_FILTERS, load);
</script>
