<template>
  <div class="min-h-screen bg-brand-bg">
    <PageContainer class="py-8">
      <!-- Header -->
      <div
        class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8"
      >
        <div>
          <h1 class="text-brand-text text-2xl font-bold">Mis Propiedades</h1>
          <p class="text-brand-muted text-sm mt-1">
            Gestiona tus propiedades publicadas
          </p>
        </div>
        <button
          @click="router.push('/properties/create')"
          class="inline-flex items-center gap-2 px-5 py-3 bg-brand-primary text-white text-sm font-semibold rounded-xl hover:bg-green-600 transition-colors"
        >
          <Plus class="w-5 h-5" />
          Nueva propiedad
        </button>
      </div>

      <FilterTabs
        :model-value="activeTab"
        :tabs="tabs"
        :get-count="getTabCount"
        @update:model-value="(v) => (activeTab = v as TabValue)"
      />

      <!-- Loading -->
      <div v-if="isLoading" class="flex items-center justify-center py-20">
        <BaseSpinner class="h-8 w-8 text-brand-primary" />
      </div>

      <!-- Empty State -->
      <EmptyState
        v-else-if="filteredProperties.length === 0"
        :title="emptyStateTitle"
        :description="emptyStateDescription"
      >
        <template #icon>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            class="text-brand-muted"
          >
            <path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8" />
            <path
              d="M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"
            />
          </svg>
        </template>
        <button
          v-if="activeTab === 'all'"
          @click="router.push('/properties/create')"
          class="inline-flex items-center gap-2 px-5 py-3 bg-brand-primary text-white text-sm font-semibold rounded-xl hover:bg-green-600 transition-colors"
        >
          <Plus class="w-5 h-5" />
          Publicar mi primera propiedad
        </button>
      </EmptyState>

      <!-- Grid -->
      <div
        v-else
        class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
      >
        <PropertyCard
          v-for="property in pagedItems"
          :key="property.id"
          :property="property"
          :show-favorite="false"
          :show-status="true"
          :show-actions="true"
          :show-visibility-toggle="true"
          @toggle-visibility="onToggleVisibility(property.id)"
          @click="router.push(`/listing/${property.id}`)"
          @edit="editProperty"
          @delete="confirmDelete"
        />
      </div>

      <PaginationArrows
        v-if="filteredProperties.length"
        class="mt-10"
        :has-prev="hasPrev"
        :has-next="hasNext"
        @prev="prev"
        @next="next()"
      />
    </PageContainer>

    <DeletePropertyModal
      :property-id="propertyToDelete"
      @close="propertyToDelete = null"
      @deleted="onPropertyDeleted"
    />
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import { Plus } from "@lucide/vue";
import PropertyCard from "@/components/properties/cards/PropertyCard.vue";
import BaseSpinner from "@/components/shared/BaseSpinner.vue";
import EmptyState from "@/components/shared/EmptyState.vue";
import FilterTabs from "@/components/shared/FilterTabs.vue";
import PaginationArrows from "@/components/shared/PaginationArrows.vue";
import DeletePropertyModal from "@/components/properties/dashboard/DeletePropertyModal.vue";
import PageContainer from "@/components/shared/PageContainer.vue";
import type { ListingStatus, PropertyCardUI } from "@/types/feed";
import { usePagination } from "@/composables/shared/usePagination";
import { usePropertyMapper } from "@/composables/properties/usePropertyMapper";
import { usePropertyVisibility } from "@/composables/properties/usePropertyVisibility";
import { useMyProperties } from "@/composables/properties/useMyProperties";
import { PAGE_SIZE } from "@/constants/pagination";

type TabValue = "all" | ListingStatus;

const router = useRouter();
const { properties, isLoading, fetchProperties } = useMyProperties();
const { cards } = usePropertyMapper(properties);

const activeTab = ref<TabValue>("all");
const tabs: { label: string; value: TabValue }[] = [
  { label: "Todas", value: "all" },
  { label: "Borrador", value: "draft" },
  { label: "Activas", value: "active" },
  { label: "Inactivas", value: "inactive" },
  { label: "Vendidas", value: "sold" },
  { label: "Arrendadas", value: "rented" },
];

const propertyToDelete = ref<string | null>(null);
const { toggleVisibility } = usePropertyVisibility();

const filteredProperties = computed(() => {
  if (activeTab.value === "all") return cards.value;
  return cards.value.filter((p) => p.status === activeTab.value);
});

const { pagedItems, hasPrev, hasNext, setItems, next, prev } =
  usePagination<PropertyCardUI>(PAGE_SIZE.MY_PROPERTIES);

watch(filteredProperties, (items) => setItems(items));

const getTabCount = (tab: string) => {
  if (tab === "all") return properties.value.length;
  return properties.value.filter((p) => p.status === tab).length;
};

const emptyStateTitle = computed(() =>
  activeTab.value === "all"
    ? "No tienes propiedades"
    : "No tienes propiedades con este estado"
);

const emptyStateDescription = computed(() => {
  if (activeTab.value === "all")
    return "Publica tu primera propiedad y empieza a recibir interesados.";
  return "Las propiedades aparecerán aquí cuando cambien a este estado.";
});

const editProperty = (id: string) => {
  router.push(`/properties/${id}/edit`);
};

const confirmDelete = (id: string) => {
  propertyToDelete.value = id;
};

const onPropertyDeleted = (id: string) => {
  properties.value = properties.value.filter((p) => p.id !== id);
  propertyToDelete.value = null;
};

onMounted(() => {
  fetchProperties();
});

const onToggleVisibility = async (property_id: string) => {
  const success = await toggleVisibility(property_id);
  if (!success) return;

  const prop = properties.value.find((p) => p.id === property_id);
  if (prop) {
    prop.status = prop.status === "active" ? "draft" : "active";
  }
};
</script>
