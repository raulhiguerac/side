<template>
  <div class="rounded-2xl border border-brand-divider bg-white p-5">
    <EmptyState
      v-if="!neighborhoodId"
      title="Sin selección"
      description="Elige un barrio de la tabla para ver su geometría."
    />

    <p v-else-if="error" class="text-sm text-brand-danger">{{ error }}</p>

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
        <AdminStatusBadge class="shrink-0" :active="detail.is_active" />
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
import { computed, watch } from "vue";
import { Ban, Pencil, RotateCcw, Upload } from "@lucide/vue";
import NeighborhoodMap from "@/components/admin/catalog/neighborhoods/widgets/NeighborhoodMap.vue";
import AdminActionBar from "@/components/admin/shared/AdminActionBar.vue";
import AdminStatusBadge from "@/components/admin/shared/AdminStatusBadge.vue";
import BaseSpinner from "@/components/shared/BaseSpinner.vue";
import EmptyState from "@/components/shared/EmptyState.vue";
import { useNeighborhoodNeighbors } from "@/composables/admin/useNeighborhoodNeighbors";
import type { AdminAction } from "@/types/admin/actions";
import type {
  NeighborhoodAction,
  NeighborhoodAdminDetail,
} from "@/types/admin/catalog";
import { formatArea } from "@/utils/number";

const props = defineProps<{
  neighborhoodId: string | null;
  detail: NeighborhoodAdminDetail | null;
  loading: boolean;
  error: string | null;
}>();

defineEmits<{ action: [key: NeighborhoodAction] }>();

const ACTIONS = computed<readonly AdminAction<NeighborhoodAction>[]>(() => [
  { key: "edit", icon: Pencil, label: "Editar" },
  { key: "geometry", icon: Upload, label: "Geometría" },
  props.detail?.is_active === false
    ? { key: "status", icon: RotateCcw, label: "Reactivar" }
    : { key: "status", icon: Ban, label: "Desactivar", variant: "danger" },
]);

const { neighbors, load: loadNeighbors, clear } = useNeighborhoodNeighbors();

const center = computed<[number, number]>(() =>
  props.detail ? [props.detail.latitude, props.detail.longitude] : [0, 0]
);

/** Los vecinos del barrio anterior no deben quedar pintados mientras llega el nuevo. */
watch(() => props.neighborhoodId, clear);
</script>
