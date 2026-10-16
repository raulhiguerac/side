<template>
  <div class="rounded-2xl border border-brand-divider bg-white p-5">
    <EmptyState
      v-if="!country"
      title="Sin selección"
      description="Elige un país de la tabla para ver su detalle."
    />

    <template v-else>
      <div class="mb-4 flex items-start justify-between gap-3">
        <div class="min-w-0">
          <h2 class="truncate text-lg font-bold text-brand-text">
            {{ country.name }}
          </h2>
          <p class="text-sm text-brand-muted">
            {{ country.iso_alpha2 }} · {{ country.iso_alpha3 }} ·
            {{ country.iso_numeric }}
          </p>
        </div>
        <AdminStatusBadge class="shrink-0" :active="country.is_active" />
      </div>

      <dl class="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
        <div v-for="field in fields" :key="field.label">
          <dt class="text-brand-muted">{{ field.label }}</dt>
          <dd class="font-medium text-brand-text">{{ field.value }}</dd>
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
import { Ban, MapIcon, Pencil, RotateCcw } from "@lucide/vue";
import AdminActionBar from "@/components/admin/shared/AdminActionBar.vue";
import AdminStatusBadge from "@/components/admin/shared/AdminStatusBadge.vue";
import EmptyState from "@/components/shared/EmptyState.vue";
import type { AdminAction } from "@/types/admin/actions";
import type { CountryAction, CountryAdminRow } from "@/types/admin/catalog";

const props = defineProps<{ country: CountryAdminRow | null }>();

defineEmits<{ action: [key: CountryAction] }>();

const ACTIONS = computed<readonly AdminAction<CountryAction>[]>(() => [
  { key: "edit", icon: Pencil, label: "Editar" },
  props.country?.is_active === false
    ? { key: "status", icon: RotateCcw, label: "Reactivar" }
    : { key: "status", icon: Ban, label: "Desactivar", variant: "danger" },
  { key: "divisions", icon: MapIcon, label: "Divisiones" },
]);

const fields = computed(() => {
  const country = props.country;
  if (!country) return [];
  return [
    { label: "Nombre oficial", value: country.official_name ?? "—" },
    { label: "Nombre nativo", value: country.native_name ?? "—" },
    { label: "Prefijo", value: country.phone_code },
    { label: "Moneda", value: country.currency_code },
    { label: "Idioma", value: country.default_locale },
    { label: "Zona horaria", value: country.default_timezone },
    { label: "Soporte", value: country.is_supported ? "Soportado" : "No" },
  ];
});
</script>
