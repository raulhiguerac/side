<template>
  <div class="mb-4 grid grid-cols-1 gap-4 lg:grid-cols-[4fr_1fr]">
    <AdminFilterBar
      :filters="COUNTRY_FILTERS"
      :initial="urlFilters"
      @apply="pushFilters"
    />

    <div
      class="border-brand-divider flex flex-col justify-center gap-2 rounded-2xl border bg-white p-4"
    >
      <BaseButton @click="creating = true">
        <Plus class="h-4 w-4 shrink-0" />
        <span class="truncate">Crear país</span>
      </BaseButton>
    </div>
  </div>

  <AdminSplitView :error="error">
    <template #table>
      <AdminCountriesTable
        :rows="rows"
        :loading="loading"
        :selected-id="selectedId"
        @row-click="selectedId = $event.id"
      />
    </template>

    <template #panel>
      <AdminCountryPanel :country="selected" @action="onAction" />
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

  <EditCountryModal
    :country="activeAction === 'edit' ? selected : null"
    @close="activeAction = null"
    @confirm="onSaved"
  />

  <CountryStatusModal
    :country="activeAction === 'status' ? selected : null"
    @close="activeAction = null"
    @confirm="onSaved"
  />

  <CreateCountryModal
    :open="creating"
    @close="creating = false"
    @confirm="onCreated"
  />
</template>

<script lang="ts" setup>
import BaseButton from "@/components/shared/BaseButton.vue";
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { Plus } from "@lucide/vue";
import AdminCountriesTable from "@/components/admin/catalog/countries/AdminCountriesTable.vue";
import AdminCountryPanel from "@/components/admin/catalog/countries/AdminCountryPanel.vue";
import CountryStatusModal from "@/components/admin/catalog/countries/modals/CountryStatusModal.vue";
import CreateCountryModal from "@/components/admin/catalog/countries/modals/CreateCountryModal.vue";
import EditCountryModal from "@/components/admin/catalog/countries/modals/EditCountryModal.vue";
import AdminFilterBar from "@/components/admin/shared/AdminFilterBar.vue";
import AdminPaginationFooter from "@/components/admin/shared/AdminPaginationFooter.vue";
import AdminSplitView from "@/components/admin/shared/AdminSplitView.vue";
import { useAdminCountries } from "@/composables/admin/useAdminCountries";
import { useRowSelection } from "@/composables/admin/useRowSelection";
import { useUrlFilters } from "@/composables/admin/useUrlFilters";
import { COUNTRY_FILTERS } from "@/constants/catalogFilters";
import type { CountryAction } from "@/types/admin/catalog";

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
} = useAdminCountries();

const { selectedId } = useRowSelection(rows);

// La fila ya trae todo lo que muestra el panel: no hay GET de detalle.
const selected = computed(
  () => rows.value.find((row) => row.id === selectedId.value) ?? null
);

const { urlFilters, pushFilters } = useUrlFilters(COUNTRY_FILTERS, load);

const activeAction = ref<Exclude<CountryAction, "divisions"> | null>(null);
const creating = ref(false);

function onAction(action: CountryAction) {
  const country = selected.value;
  if (action !== "divisions") {
    activeAction.value = action;
    return;
  }
  if (!country) return;
  router.push({
    name: "admin-catalog-admin-divisions",
    query: { country_id: country.id },
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
