<template>
  <div class="mb-4 grid grid-cols-1 gap-4 lg:grid-cols-[4fr_1fr]">
    <AdminFilterBar
      :filters="LOCALITY_FILTERS"
      :initial="urlFilters"
      @apply="pushFilters"
    />

    <div
      class="border-brand-divider flex flex-col justify-center gap-2 rounded-2xl border bg-white p-4"
    >
      <button
        type="button"
        class="border-brand-primary bg-brand-primary flex items-center gap-2 rounded-xl border px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-green-600"
        @click="creating = true"
      >
        <Plus class="h-4 w-4 shrink-0" />
        <span class="truncate">Crear localidad</span>
      </button>
    </div>
  </div>

  <AdminSplitView :error="error">
    <template #table>
      <AdminLocalitiesTable
        :rows="rows"
        :loading="loading"
        :selected-id="selectedId"
        @row-click="selectedId = $event.id"
      />
    </template>

    <template #panel>
      <AdminLocalityPanel :locality="selected" @action="onAction" />
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

  <EditLocalityModal
    :locality="activeAction === 'edit' ? selected : null"
    @close="activeAction = null"
    @confirm="onSaved"
  />

  <LocalityStatusModal
    :locality="activeAction === 'status' ? selected : null"
    @close="activeAction = null"
    @confirm="onSaved"
  />

  <CreateLocalityModal
    :open="creating"
    :initial-country-id="urlFilters.country_id || null"
    :initial-division-id="urlFilters.admin_division_id || null"
    @close="creating = false"
    @confirm="onCreated"
  />
</template>

<script lang="ts" setup>
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { Plus } from "@lucide/vue";
import AdminLocalitiesTable from "@/components/admin/catalog/localities/AdminLocalitiesTable.vue";
import AdminLocalityPanel from "@/components/admin/catalog/localities/AdminLocalityPanel.vue";
import CreateLocalityModal from "@/components/admin/catalog/localities/modals/CreateLocalityModal.vue";
import EditLocalityModal from "@/components/admin/catalog/localities/modals/EditLocalityModal.vue";
import LocalityStatusModal from "@/components/admin/catalog/localities/modals/LocalityStatusModal.vue";
import AdminFilterBar from "@/components/admin/shared/AdminFilterBar.vue";
import AdminPaginationFooter from "@/components/admin/shared/AdminPaginationFooter.vue";
import AdminSplitView from "@/components/admin/shared/AdminSplitView.vue";
import { useAdminLocalities } from "@/composables/admin/useAdminLocalities";
import { useRowSelection } from "@/composables/admin/useRowSelection";
import { useUrlFilters } from "@/composables/admin/useUrlFilters";
import { LOCALITY_FILTERS } from "@/constants/catalogFilters";
import type { LocalityAction } from "@/types/admin/catalog";

const router = useRouter();

const {
  rows,
  totalItems,
  hasPrev,
  hasNext,
  range,
  loading,
  error,
  load,
  reload,
  next,
  prev,
} = useAdminLocalities();

const { selectedId } = useRowSelection(rows);

// La fila ya trae todo lo que muestra el panel: no hay GET de detalle.
const selected = computed(
  () => rows.value.find((row) => row.id === selectedId.value) ?? null
);

const { urlFilters, pushFilters } = useUrlFilters(LOCALITY_FILTERS, load);

const activeAction = ref<Exclude<LocalityAction, "neighborhoods"> | null>(null);
const creating = ref(false);

function onAction(action: LocalityAction) {
  const locality = selected.value;
  if (action !== "neighborhoods") {
    activeAction.value = action;
    return;
  }
  if (!locality) return;
  // La tab de barrios filtra por URL: el país hace falta para su cascada.
  router.push({
    name: "admin-catalog",
    query: { country_id: locality.country_id, locality_id: locality.id },
  });
}

async function onSaved() {
  activeAction.value = null;
  await reload();
}

async function onCreated() {
  creating.value = false;
  await reload();
}
</script>
