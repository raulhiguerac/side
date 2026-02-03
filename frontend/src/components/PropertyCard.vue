<template>
  <div
    class="bg-white rounded-2xl border border-brand-divider overflow-hidden hover:shadow-lg transition-shadow group"
  >
    <!-- Image -->
    <div class="relative h-48 overflow-hidden">
      <img
        :src="property.image || defaultImage"
        :alt="property.title"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
      />

      <!-- Badge de tipo -->
      <div
        class="absolute top-3 left-3 px-3 py-1 rounded-full text-xs font-semibold"
        :class="typeBadgeClass"
      >
        {{ typeLabel }}
      </div>

      <!-- Favorito -->
      <button
        v-if="showFavorite"
        @click.stop="$emit('toggle-favorite', property.id)"
        class="absolute top-3 right-3 w-8 h-8 bg-white/90 rounded-full flex items-center justify-center hover:bg-white transition-colors"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="18"
          height="18"
          viewBox="0 0 24 24"
          :fill="property.isFavorite ? 'currentColor' : 'none'"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          :class="property.isFavorite ? 'text-red-500' : 'text-brand-muted'"
        >
          <path
            d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"
          />
        </svg>
      </button>

      <!-- Status badge (para propiedades del usuario) -->
      <div
        v-if="showStatus && property.status"
        class="absolute bottom-3 left-3 px-3 py-1 rounded-full text-xs font-semibold"
        :class="statusBadgeClass"
      >
        {{ statusLabel }}
      </div>
    </div>

    <!-- Content -->
    <div class="p-4">
      <!-- Price -->
      <div class="flex items-baseline gap-1 mb-2">
        <span class="text-brand-text text-xl font-bold">
          ${{ formatPrice(property.price) }}
        </span>
        <span v-if="property.type === 'rent'" class="text-brand-muted text-sm"
          >/mes</span
        >
      </div>

      <!-- Title -->
      <h3 class="text-brand-text font-semibold text-sm mb-2 line-clamp-1">
        {{ property.title }}
      </h3>

      <!-- Location -->
      <div class="flex items-center gap-1.5 text-brand-muted text-sm mb-3">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
          <circle cx="12" cy="10" r="3" />
        </svg>
        <span class="line-clamp-1">{{ property.location }}</span>
      </div>

      <!-- Features -->
      <div class="flex items-center gap-4 text-brand-muted text-xs">
        <div class="flex items-center gap-1">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M2 4v16" />
            <path d="M2 8h18a2 2 0 0 1 2 2v10" />
            <path d="M2 17h20" />
            <path d="M6 8v9" />
          </svg>
          <span>{{ property.bedrooms }} hab.</span>
        </div>
        <div class="flex items-center gap-1">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              d="M9 6 6.5 3.5a1.5 1.5 0 0 0-1-.5C4.683 3 4 3.683 4 4.5V17a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-5"
            />
            <line x1="10" x2="8" y1="5" y2="7" />
            <line x1="2" x2="22" y1="12" y2="12" />
            <line x1="7" x2="7" y1="19" y2="21" />
            <line x1="17" x2="17" y1="19" y2="21" />
          </svg>
          <span>{{ property.bathrooms }} baños</span>
        </div>
        <div class="flex items-center gap-1">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <rect width="18" height="18" x="3" y="3" rx="2" />
          </svg>
          <span>{{ property.area }} m²</span>
        </div>
      </div>

      <!-- Actions (para propiedades del usuario) -->
      <div
        v-if="showActions"
        class="flex gap-2 mt-4 pt-4 border-t border-brand-divider"
      >
        <button
          @click.stop="$emit('edit', property.id)"
          class="flex-1 py-2 px-3 bg-brand-bg text-brand-text text-sm font-medium rounded-lg hover:bg-brand-divider transition-colors"
        >
          Editar
        </button>
        <button
          @click.stop="$emit('delete', property.id)"
          class="py-2 px-3 text-red-500 text-sm font-medium rounded-lg hover:bg-red-50 transition-colors"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M3 6h18" />
            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed } from "vue";

export interface Property {
  id: string;
  title: string;
  price: number;
  location: string;
  image?: string;
  type: "sale" | "rent";
  status?: "active" | "inactive" | "pending";
  bedrooms: number;
  bathrooms: number;
  area: number;
  isFavorite?: boolean;
}

const props = withDefaults(
  defineProps<{
    property: Property;
    showFavorite?: boolean;
    showStatus?: boolean;
    showActions?: boolean;
  }>(),
  {
    showFavorite: true,
    showStatus: false,
    showActions: false,
  }
);

defineEmits<{
  (e: "toggle-favorite", id: string): void;
  (e: "edit", id: string): void;
  (e: "delete", id: string): void;
}>();

const defaultImage =
  "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=400&h=300&fit=crop";

const typeLabel = computed(() =>
  props.property.type === "sale" ? "Venta" : "Arriendo"
);

const typeBadgeClass = computed(() =>
  props.property.type === "sale"
    ? "bg-brand-primary text-white"
    : "bg-blue-500 text-white"
);

const statusLabel = computed(() => {
  switch (props.property.status) {
    case "active":
      return "Activa";
    case "inactive":
      return "Inactiva";
    case "pending":
      return "Pendiente";
    default:
      return "";
  }
});

const statusBadgeClass = computed(() => {
  switch (props.property.status) {
    case "active":
      return "bg-green-500 text-white";
    case "inactive":
      return "bg-gray-500 text-white";
    case "pending":
      return "bg-yellow-500 text-white";
    default:
      return "";
  }
});

const formatPrice = (price: number) => {
  return price.toLocaleString("es-CO");
};
</script>
