<template>
  <div class="min-h-screen bg-brand-bg">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
          @click="$router.push('/properties/new')"
          class="inline-flex items-center gap-2 px-5 py-3 bg-brand-primary text-white text-sm font-semibold rounded-xl hover:bg-green-600 transition-colors"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M5 12h14" />
            <path d="M12 5v14" />
          </svg>
          Nueva propiedad
        </button>
      </div>

      <!-- Tabs -->
      <div class="flex gap-2 mb-6 overflow-x-auto pb-2">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          @click="activeTab = tab.value"
          class="px-4 py-2 rounded-lg text-sm font-medium transition-all flex-shrink-0"
          :class="
            activeTab === tab.value
              ? 'bg-brand-primary text-white'
              : 'bg-white text-brand-text hover:bg-brand-bg'
          "
        >
          {{ tab.label }}
          <span
            class="ml-1.5 px-2 py-0.5 rounded-full text-xs"
            :class="
              activeTab === tab.value
                ? 'bg-white/20 text-white'
                : 'bg-brand-bg text-brand-muted'
            "
          >
            {{ getTabCount(tab.value) }}
          </span>
        </button>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="flex items-center justify-center py-20">
        <svg
          class="animate-spin h-8 w-8 text-brand-primary"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          />
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="filteredProperties.length === 0"
        class="bg-white rounded-2xl border border-brand-divider p-12 text-center"
      >
        <div
          class="w-16 h-16 bg-brand-bg rounded-full flex items-center justify-center mx-auto mb-4"
        >
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
        </div>
        <h3 class="text-brand-text font-semibold text-lg mb-2">
          {{ emptyStateTitle }}
        </h3>
        <p class="text-brand-muted text-sm mb-6">
          {{ emptyStateDescription }}
        </p>
        <button
          v-if="activeTab === 'all'"
          @click="$router.push('/properties/new')"
          class="inline-flex items-center gap-2 px-5 py-3 bg-brand-primary text-white text-sm font-semibold rounded-xl hover:bg-green-600 transition-colors"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M5 12h14" />
            <path d="M12 5v14" />
          </svg>
          Publicar mi primera propiedad
        </button>
      </div>

      <!-- Grid -->
      <div
        v-else
        class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
      >
        <PropertyCard
          v-for="property in filteredProperties"
          :key="property.id"
          :property="property"
          :show-favorite="false"
          :show-status="true"
          :show-actions="true"
          @edit="editProperty"
          @delete="confirmDelete"
        />
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div
      v-if="showDeleteModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click.self="showDeleteModal = false"
    >
      <div class="bg-white rounded-2xl max-w-md w-full p-6">
        <div class="flex items-center gap-4 mb-4">
          <div
            class="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              class="text-red-600"
            >
              <path d="M3 6h18" />
              <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
              <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
            </svg>
          </div>
          <div>
            <h3 class="text-brand-text font-bold text-lg">
              Eliminar propiedad
            </h3>
          </div>
        </div>

        <p class="text-brand-muted text-sm mb-6">
          ¿Estás seguro de que deseas eliminar esta propiedad? Esta acción no se
          puede deshacer.
        </p>

        <div class="flex gap-3">
          <button
            @click="showDeleteModal = false"
            class="flex-1 py-3 rounded-xl text-sm font-semibold text-brand-text hover:bg-brand-bg transition-colors"
          >
            Cancelar
          </button>
          <button
            @click="deleteProperty"
            :disabled="isDeleting"
            class="flex-1 py-3 bg-red-500 text-white rounded-xl text-sm font-semibold hover:bg-red-600 transition-colors"
          >
            {{ isDeleting ? "Eliminando..." : "Eliminar" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import PropertyCard from "@/components/properties/PropertyCard.vue";
import type { PropertyCardUI } from "@/types/feed";
import axios from "axios";

const router = useRouter();
const isLoading = ref(true);
const properties = ref<PropertyCardUI[]>([]);

const activeTab = ref<"all" | "active" | "inactive" | "pending">("all");
const tabs = [
  { label: "Todas", value: "all" as const },
  { label: "Activas", value: "active" as const },
  { label: "Inactivas", value: "inactive" as const },
  { label: "Pendientes", value: "pending" as const },
];

const showDeleteModal = ref(false);
const propertyToDelete = ref<string | null>(null);
const isDeleting = ref(false);

const filteredProperties = computed(() => {
  if (activeTab.value === "all") return properties.value;
  return properties.value.filter((p) => p.status === activeTab.value);
});

const getTabCount = (tab: string) => {
  if (tab === "all") return properties.value.length;
  return properties.value.filter((p) => p.status === tab).length;
};

const emptyStateTitle = computed(() => {
  if (activeTab.value === "all") return "No tienes propiedades";
  return `No tienes propiedades ${
    activeTab.value === "active"
      ? "activas"
      : activeTab.value === "inactive"
      ? "inactivas"
      : "pendientes"
  }`;
});

const emptyStateDescription = computed(() => {
  if (activeTab.value === "all")
    return "Publica tu primera propiedad y empieza a recibir interesados.";
  return "Las propiedades aparecerán aquí cuando cambien a este estado.";
});

const fetchProperties = async () => {
  isLoading.value = true;
  try {
    const response = await axios.get("http://localhost:8000/v1/properties/me", {
      withCredentials: true,
    });
    properties.value = response.data.properties || [];
  } catch (error) {
    console.error("Error al cargar propiedades:", error);
    // Mock data para desarrollo
    properties.value = [
      {
        id: "1",
        title: "Apartamento moderno en Chapinero",
        price: 450000000,
        location: "Chapinero, Bogotá",
        type: "sale",
        status: "active",
        bedrooms: 3,
        bathrooms: 2,
        area: 85,
        image:
          "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=400",
      },
      {
        id: "2",
        title: "Casa campestre en La Calera",
        price: 3500000,
        location: "La Calera, Cundinamarca",
        type: "rent",
        status: "active",
        bedrooms: 4,
        bathrooms: 3,
        area: 200,
        image:
          "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=400",
      },
      {
        id: "3",
        title: "Oficina en zona financiera",
        price: 280000000,
        location: "Centro Internacional, Bogotá",
        type: "sale",
        status: "pending",
        bedrooms: 0,
        bathrooms: 2,
        area: 120,
        image:
          "https://images.unsplash.com/photo-1497366216548-37526070297c?w=400",
      },
    ];
  } finally {
    isLoading.value = false;
  }
};

const editProperty = (id: string) => {
  router.push(`/properties/${id}/edit`);
};

const confirmDelete = (id: string) => {
  propertyToDelete.value = id;
  showDeleteModal.value = true;
};

const deleteProperty = async () => {
  if (!propertyToDelete.value) return;

  isDeleting.value = true;
  try {
    await axios.delete(
      `http://localhost:8000/v1/properties/${propertyToDelete.value}`,
      { withCredentials: true }
    );
    properties.value = properties.value.filter(
      (p) => p.id !== propertyToDelete.value
    );
  } catch (error) {
    console.error("Error al eliminar propiedad:", error);
    alert("Error al eliminar la propiedad");
  } finally {
    isDeleting.value = false;
    showDeleteModal.value = false;
    propertyToDelete.value = null;
  }
};

onMounted(() => {
  fetchProperties();
});
</script>
