<template>
  <div class="mb-4 grid grid-cols-1 gap-4 lg:grid-cols-[4fr_1fr]">
    <AdminFilterBar
      :filters="DIVISION_FILTERS"
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
        <span class="truncate">Crear división</span>
      </button>
    </div>
  </div>

  <AdminSplitView :error="error">
    <template #table>
      <AdminDivisionsTable
        :rows="rows"
        :loading="loading"
        :selected-id="selectedId"
        @row-click="selectedId = $event.id"
      />
    </template>

    <template #panel>
      <AdminDivisionPanel :division="selected" @action="onAction" />
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

  <EditDivisionModal
    :division="activeAction === 'edit' ? selected : null"
    @close="activeAction = null"
    @confirm="onSaved"
  />

  <DivisionStatusModal
    :division="activeAction === 'status' ? selected : null"
    @close="activeAction = null"
    @confirm="onSaved"
  />

  <CreateDivisionModal
    :open="creating"
    :initial-country-id="urlFilters.country_id || null"
    @close="creating = false"
    @confirm="onCreated"
  />
</template>

<script lang="ts" setup>
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { Plus } from "@lucide/vue";
import AdminDivisionPanel from "@/components/admin/catalog/divisions/AdminDivisionPanel.vue";
import AdminDivisionsTable from "@/components/admin/catalog/divisions/AdminDivisionsTable.vue";
import CreateDivisionModal from "@/components/admin/catalog/divisions/modals/CreateDivisionModal.vue";
import DivisionStatusModal from "@/components/admin/catalog/divisions/modals/DivisionStatusModal.vue";
import EditDivisionModal from "@/components/admin/catalog/divisions/modals/EditDivisionModal.vue";
import AdminFilterBar from "@/components/admin/shared/AdminFilterBar.vue";
import AdminPaginationFooter from "@/components/admin/shared/AdminPaginationFooter.vue";
import AdminSplitView from "@/components/admin/shared/AdminSplitView.vue";
import { useAdminDivisions } from "@/composables/admin/useAdminDivisions";
import { useRowSelection } from "@/composables/admin/useRowSelection";
import { useUrlFilters } from "@/composables/admin/useUrlFilters";
import { DIVISION_FILTERS } from "@/constants/catalogFilters";
import type { DivisionAction } from "@/types/admin/catalog";

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
} = useAdminDivisions();

const { selectedId } = useRowSelection(rows);

// La fila ya trae todo lo que muestra el panel: no hay GET de detalle.
const selected = computed(
  () => rows.value.find((row) => row.id === selectedId.value) ?? null
);

const { urlFilters, pushFilters } = useUrlFilters(DIVISION_FILTERS, load);

const activeAction = ref<Exclude<DivisionAction, "localities"> | null>(null);
const creating = ref(false);

function onAction(action: DivisionAction) {
  const division = selected.value;
  if (action !== "localities") {
    activeAction.value = action;
    return;
  }
  if (!division) return;
  // La tab de localidades filtra por URL: el país hace falta para su cascada.
  router.push({
    name: "admin-catalog-localities",
    query: { country_id: division.country_id, admin_division_id: division.id },
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
