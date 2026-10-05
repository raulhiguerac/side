<template>
  <!-- Arriba del split y no en su slot: la cascada filtra la tabla y también el mapa. -->
  <AdminFilterBar
    class="mb-4"
    filters-width="full"
    :filters="NEIGHBORHOOD_FILTERS"
    :initial="urlFilters"
    @apply="onApplyFilters"
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
      <AdminNeighborhoodPanel :neighborhood-id="selectedId" />
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
</template>

<script lang="ts" setup>
import { computed, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import catalogApi from "@/api/catalogApi";
import AdminNeighborhoodPanel from "@/components/admin/catalog/neighborhoods/AdminNeighborhoodPanel.vue";
import AdminNeighborhoodsTable from "@/components/admin/catalog/neighborhoods/AdminNeighborhoodsTable.vue";
import NeighborhoodCoverageBar from "@/components/admin/catalog/neighborhoods/NeighborhoodCoverageBar.vue";
import AdminFilterBar from "@/components/admin/shared/AdminFilterBar.vue";
import AdminSplitView from "@/components/admin/shared/AdminSplitView.vue";
import PaginationArrows from "@/components/shared/PaginationArrows.vue";
import { useAdminNeighborhoods } from "@/composables/admin/useAdminNeighborhoods";
import { useRowSelection } from "@/composables/admin/useRowSelection";
import { CATALOG_ENDPOINTS } from "@/constants/catalogEndpoints";
import type {
  AdminFilterDefinition,
  AdminFilterOptions,
} from "@/types/admin/filters";
import { sanitizeFilterQuery } from "@/utils/adminFilters";

type CatalogItem = { id: string; name: string };

const toOptions = (items: CatalogItem[]): AdminFilterOptions =>
  Object.fromEntries(items.map((item) => [item.id, item.name]));

/** País y localidad salen de los GET públicos, que solo traen activos: falta el
 * GET admin de la cascada, y con él la división. */
const NEIGHBORHOOD_FILTERS: readonly AdminFilterDefinition[] = [
  {
    type: "async-select",
    key: "country_id",
    label: "País",
    allLabel: "Todos",
    loadOptions: async () => {
      const { data } = await catalogApi.get<CatalogItem[]>(
        CATALOG_ENDPOINTS.countries
      );
      return toOptions(data);
    },
  },
  {
    type: "async-select",
    key: "locality_id",
    label: "Localidad",
    dependsOn: "country_id",
    loadOptions: async ({ country_id }) => {
      const { data } = await catalogApi.get<CatalogItem[]>(
        CATALOG_ENDPOINTS.localitiesByCountry,
        { params: { country_id } }
      );
      return toOptions(data);
    },
  },
  {
    key: "is_active",
    label: "Estado",
    options: { true: "Activo", false: "Inactivo" },
    allLabel: "Todos",
  },
  {
    key: "has_geometry",
    label: "Geometría",
    options: { true: "Con geometría", false: "Sin geometría" },
  },
  {
    type: "search",
    key: "search_term",
    label: "Buscar",
    placeholder: "Nombre del barrio",
  },
];

const route = useRoute();
const router = useRouter();

const urlFilters = computed(() =>
  sanitizeFilterQuery(route.query, NEIGHBORHOOD_FILTERS)
);

function onApplyFilters(values: Record<string, string>) {
  router.push({ query: values });
}

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

watch(urlFilters, load, { immediate: true });
</script>
