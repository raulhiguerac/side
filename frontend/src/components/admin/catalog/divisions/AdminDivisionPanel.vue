<template>
  <div class="rounded-2xl border border-brand-divider bg-white p-5">
    <EmptyState
      v-if="!division"
      title="Sin selección"
      description="Elige una división de la tabla para ver su detalle."
    />

    <template v-else>
      <div class="mb-4 flex items-start justify-between gap-3">
        <div class="min-w-0">
          <h2 class="truncate text-lg font-bold text-brand-text">
            {{ division.name }}
          </h2>
          <p class="text-sm text-brand-muted">
            Código {{ division.code }} · {{ division.type_name }}
          </p>
        </div>
        <AdminStatusBadge class="shrink-0" :active="division.is_active" />
      </div>

      <dl class="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
        <div>
          <dt class="text-brand-muted">Tipo</dt>
          <dd class="font-medium text-brand-text">{{ division.type_name }}</dd>
        </div>
        <div>
          <dt class="text-brand-muted">ISO 3166-2</dt>
          <dd class="font-medium text-brand-text">
            {{ division.iso_code ?? "—" }}
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
import { computed } from "vue";
import { Ban, MapPinned, Pencil, RotateCcw } from "@lucide/vue";
import AdminActionBar from "@/components/admin/shared/AdminActionBar.vue";
import AdminStatusBadge from "@/components/admin/shared/AdminStatusBadge.vue";
import EmptyState from "@/components/shared/EmptyState.vue";
import type { AdminAction } from "@/types/admin/actions";
import type { DivisionAction, DivisionAdminRow } from "@/types/admin/catalog";

const props = defineProps<{ division: DivisionAdminRow | null }>();

defineEmits<{ action: [key: DivisionAction] }>();

const ACTIONS = computed<readonly AdminAction<DivisionAction>[]>(() => [
  { key: "edit", icon: Pencil, label: "Editar" },
  props.division?.is_active === false
    ? { key: "status", icon: RotateCcw, label: "Reactivar" }
    : { key: "status", icon: Ban, label: "Desactivar", variant: "danger" },
  { key: "localities", icon: MapPinned, label: "Localidades" },
]);
</script>
