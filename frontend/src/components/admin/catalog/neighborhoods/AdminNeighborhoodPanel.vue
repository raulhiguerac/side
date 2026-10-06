<template>
  <div class="rounded-2xl border border-brand-divider bg-white p-5">
    <EmptyState
      v-if="!neighborhoodId"
      title="Sin selección"
      description="Elige un barrio de la tabla para ver su geometría."
    />

    <p v-else-if="error" class="text-sm text-red-600">{{ error }}</p>

    <div v-else-if="loading && !detail" class="flex justify-center py-16">
      <BaseSpinner class="h-6 w-6 text-brand-primary" />
    </div>

    <template v-else-if="detail">
      <div class="mb-4 flex items-start justify-between gap-3">
        <div class="min-w-0">
          <h2 class="truncate text-lg font-bold text-brand-text">
            {{ detail.name }}
          </h2>
          <p class="text-sm text-brand-muted">Código {{ detail.code }}</p>
        </div>
        <span
          :class="[
            'inline-flex shrink-0 items-center rounded-full px-2.5 py-1 text-xs font-medium',
            detail.is_active
              ? 'bg-brand-primary-light text-green-700'
              : 'bg-gray-100 text-brand-muted',
          ]"
        >
          {{ detail.is_active ? "Activo" : "Inactivo" }}
        </span>
      </div>

      <NeighborhoodMap
        :geometry="detail.geometry"
        :center="center"
        :neighbors="neighbors"
        @bounds="loadNeighbors(detail.id, $event)"
      />

      <p v-if="!detail.geometry" class="mt-2 text-xs text-brand-muted">
        Sin geometría: el mapa se centra en el centroide.
      </p>

      <dl class="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
        <div>
          <dt class="text-brand-muted">Área</dt>
          <dd class="font-medium text-brand-text tabular-nums">
            {{ formatArea(detail.area_m2) }}
          </dd>
        </div>
        <div>
          <dt class="text-brand-muted">Centroide</dt>
          <dd class="font-medium text-brand-text tabular-nums">
            {{ detail.latitude.toFixed(5) }}, {{ detail.longitude.toFixed(5) }}
          </dd>
        </div>
        <div>
          <dt class="text-brand-muted">Código postal</dt>
          <dd class="font-medium text-brand-text">
            {{ detail.postal_code ?? "—" }}
          </dd>
        </div>
        <div>
          <dt class="text-brand-muted">Vecinos en el mapa</dt>
          <dd class="font-medium text-brand-text tabular-nums">
            {{ neighbors.length }}
          </dd>
        </div>
      </dl>

      <AdminActionBar
        class="mt-5"
        :actions="ACTIONS"
        @action="$emit('action', $event)"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, toRef, watch } from "vue";
import { Ban, Pencil, Upload } from "@lucide/vue";
import NeighborhoodMap from "@/components/admin/catalog/neighborhoods/NeighborhoodMap.vue";
import AdminActionBar from "@/components/admin/shared/AdminActionBar.vue";
import BaseSpinner from "@/components/shared/BaseSpinner.vue";
import EmptyState from "@/components/shared/EmptyState.vue";
import { useNeighborhoodDetail } from "@/composables/admin/useNeighborhoodDetail";
import { useNeighborhoodNeighbors } from "@/composables/admin/useNeighborhoodNeighbors";
import type { AdminAction } from "@/types/admin/actions";
import type { NeighborhoodAction } from "@/types/admin/catalog";

const props = defineProps<{ neighborhoodId: string | null }>();

defineEmits<{ action: [key: NeighborhoodAction] }>();

const ACTIONS: readonly AdminAction<NeighborhoodAction>[] = [
  { key: "edit", icon: Pencil, label: "Editar" },
  { key: "geometry", icon: Upload, label: "Geometría" },
  { key: "deactivate", icon: Ban, label: "Desactivar", variant: "danger" },
];

const { detail, loading, error } = useNeighborhoodDetail(
  toRef(props, "neighborhoodId")
);
const { neighbors, load: loadNeighbors, clear } = useNeighborhoodNeighbors();

const center = computed<[number, number]>(() =>
  detail.value ? [detail.value.latitude, detail.value.longitude] : [0, 0]
);

/** Los vecinos del barrio anterior no deben quedar pintados mientras llega el nuevo. */
watch(() => props.neighborhoodId, clear);

function formatArea(m2: number | null): string {
  if (m2 == null) return "—";
  if (m2 < 1_000_000) return `${Math.round(m2).toLocaleString("es-CO")} m²`;
  return `${(m2 / 1_000_000).toLocaleString("es-CO", {
    maximumFractionDigits: 2,
  })} km²`;
}
</script>
