<template>
  <!-- Arriba del split y no en su slot: la cascada filtra la tabla y también el mapa. -->
  <div class="mb-4 grid grid-cols-1 gap-4 lg:grid-cols-[4fr_1fr]">
    <AdminFilterBar
      :filters="NEIGHBORHOOD_FILTERS"
      :initial="urlFilters"
      @apply="pushFilters"
    />

    <div
      class="border-brand-divider flex flex-col justify-center gap-2 rounded-2xl border bg-white p-4"
    >
      <BaseButton @click="creating = true">
        <Plus class="h-4 w-4 shrink-0" />
        <span class="truncate">Crear barrio</span>
      </BaseButton>

      <BaseButton
        v-for="action in BULK_ACTIONS"
        :key="action.key"
        variant="secondary"
        @click="bulkModal = action.key"
      >
        <component :is="action.icon" class="h-4 w-4 shrink-0" />
        <span class="truncate">{{ action.label }}</span>
      </BaseButton>
    </div>
  </div>

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
        :detail="detail"
        :loading="detailLoading"
        :error="detailError"
        @action="activeAction = $event"
      />
    </template>

    <template #footer>
      <AdminPaginationFooter
        :range="range"
        :total="totalItems"
        :has-prev="hasPrev"
        :has-next="hasNext"
        @prev="prev"
        @next="next"
      />
    </template>
  </AdminSplitView>

  <EditNeighborhoodModal
    :neighborhood="activeAction === 'edit' ? detail : null"
    @close="activeAction = null"
    @confirm="onSaved"
  />

  <NeighborhoodStatusModal
    :neighborhood="activeAction === 'status' ? detail : null"
    @close="activeAction = null"
    @confirm="onSaved"
  />

  <CreateNeighborhoodModal
    :open="creating"
    :initial-country-id="urlFilters.country_id || null"
    :initial-locality-id="urlFilters.locality_id || null"
    @close="creating = false"
    @confirm="onCreated"
  />

  <BulkNeighborhoodsModal
    :open="bulkModal === 'neighborhoods'"
    :initial-country-id="urlFilters.country_id || null"
    :initial-locality-id="urlFilters.locality_id || null"
    @close="bulkModal = null"
    @confirm="onBulkDone"
  />

  <BulkGeometriesModal
    :open="bulkModal === 'geometries'"
    :initial-country-id="urlFilters.country_id || null"
    :initial-locality-id="urlFilters.locality_id || null"
    @close="bulkModal = null"
    @confirm="onBulkDone"
  />

  <ReplaceGeometryModal
    :neighborhood="activeAction === 'geometry' ? detail : null"
    @close="activeAction = null"
    @confirm="onSaved"
  />
</template>

<script lang="ts" setup>
import BaseButton from "@/components/shared/BaseButton.vue";
import { ref } from "vue";
import { FileUp, MapPinned, Plus } from "@lucide/vue";
import AdminNeighborhoodPanel from "@/components/admin/catalog/neighborhoods/AdminNeighborhoodPanel.vue";
import AdminNeighborhoodsTable from "@/components/admin/catalog/neighborhoods/AdminNeighborhoodsTable.vue";
import BulkGeometriesModal from "@/components/admin/catalog/neighborhoods/modals/BulkGeometriesModal.vue";
import BulkNeighborhoodsModal from "@/components/admin/catalog/neighborhoods/modals/BulkNeighborhoodsModal.vue";
import CreateNeighborhoodModal from "@/components/admin/catalog/neighborhoods/modals/CreateNeighborhoodModal.vue";
import EditNeighborhoodModal from "@/components/admin/catalog/neighborhoods/modals/EditNeighborhoodModal.vue";
import NeighborhoodCoverageBar from "@/components/admin/catalog/neighborhoods/widgets/NeighborhoodCoverageBar.vue";
import NeighborhoodStatusModal from "@/components/admin/catalog/neighborhoods/modals/NeighborhoodStatusModal.vue";
import ReplaceGeometryModal from "@/components/admin/catalog/neighborhoods/modals/ReplaceGeometryModal.vue";
import AdminFilterBar from "@/components/admin/shared/AdminFilterBar.vue";
import AdminPaginationFooter from "@/components/admin/shared/AdminPaginationFooter.vue";
import AdminSplitView from "@/components/admin/shared/AdminSplitView.vue";
import { useAdminNeighborhoods } from "@/composables/admin/useAdminNeighborhoods";
import { useNeighborhoodDetail } from "@/composables/admin/useNeighborhoodDetail";
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
  reload: reloadList,
  next,
  prev,
} = useAdminNeighborhoods();

const { selectedId } = useRowSelection(rows);

const {
  detail,
  loading: detailLoading,
  error: detailError,
  reload: reloadDetail,
} = useNeighborhoodDetail(selectedId);

const activeAction = ref<NeighborhoodAction | null>(null);

const BULK_ACTIONS = [
  { key: "neighborhoods", label: "Subir barrios", icon: FileUp },
  { key: "geometries", label: "Subir geometrías", icon: MapPinned },
] as const;

const bulkModal = ref<(typeof BULK_ACTIONS)[number]["key"] | null>(null);

const { urlFilters, pushFilters } = useUrlFilters(NEIGHBORHOOD_FILTERS, load);

const creating = ref(false);

async function onCreated() {
  creating.value = false;
  await reloadList();
}

async function onBulkDone() {
  bulkModal.value = null;
  await Promise.all([reloadList(), reloadDetail()]);
}

async function onSaved() {
  activeAction.value = null;
  await Promise.all([reloadList(), reloadDetail()]);
}
</script>
