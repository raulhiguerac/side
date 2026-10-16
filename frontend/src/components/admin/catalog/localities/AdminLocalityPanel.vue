<template>
  <div class="rounded-2xl border border-brand-divider bg-white p-5">
    <EmptyState
      v-if="!locality"
      title="Sin selección"
      description="Elige una localidad de la tabla para ver su detalle."
    />

    <template v-else>
      <div class="mb-4 flex items-start justify-between gap-3">
        <div class="min-w-0">
          <h2
            class="flex items-center gap-1.5 text-lg font-bold text-brand-text"
          >
            <span class="truncate">{{ locality.name }}</span>
            <Star
              v-if="locality.is_capital"
              class="h-4 w-4 shrink-0 fill-brand-accent text-brand-accent"
              aria-label="Capital"
            />
          </h2>
          <p class="text-sm text-brand-muted">
            Código {{ locality.code }} ·
            {{ LOCALITY_TYPE_LABELS[locality.locality_type] }}
          </p>
        </div>
        <AdminStatusBadge class="shrink-0" :active="locality.is_active" />
      </div>

      <LocalityMap :center="center" />

      <dl class="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
        <div>
          <dt class="text-brand-muted">Nombre local</dt>
          <dd class="font-medium text-brand-text">
            {{ locality.local_name ?? "—" }}
          </dd>
        </div>
        <div>
          <dt class="text-brand-muted">Coordenadas</dt>
          <dd class="font-medium text-brand-text tabular-nums">
            {{ locality.point.latitude.toFixed(5) }},
            {{ locality.point.longitude.toFixed(5) }}
          </dd>
        </div>
        <div>
          <dt class="text-brand-muted">Zona horaria</dt>
          <dd class="font-medium text-brand-text">{{ locality.timezone }}</dd>
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
import { computed } from "vue";
import { Ban, MapPinned, Pencil, RotateCcw, Star } from "@lucide/vue";
import LocalityMap from "@/components/admin/catalog/localities/widgets/LocalityMap.vue";
import AdminActionBar from "@/components/admin/shared/AdminActionBar.vue";
import AdminStatusBadge from "@/components/admin/shared/AdminStatusBadge.vue";
import EmptyState from "@/components/shared/EmptyState.vue";
import { LOCALITY_TYPE_LABELS } from "@/constants/localityLabels";
import type { AdminAction } from "@/types/admin/actions";
import type { LocalityAction, LocalityAdminRow } from "@/types/admin/catalog";

const props = defineProps<{ locality: LocalityAdminRow | null }>();

defineEmits<{ action: [key: LocalityAction] }>();

const ACTIONS = computed<readonly AdminAction<LocalityAction>[]>(() => [
  { key: "edit", icon: Pencil, label: "Editar" },
  props.locality?.is_active === false
    ? { key: "status", icon: RotateCcw, label: "Reactivar" }
    : { key: "status", icon: Ban, label: "Desactivar", variant: "danger" },
  { key: "neighborhoods", icon: MapPinned, label: "Barrios" },
]);

const center = computed<[number, number]>(() =>
  props.locality
    ? [props.locality.point.latitude, props.locality.point.longitude]
    : [0, 0]
);
</script>
