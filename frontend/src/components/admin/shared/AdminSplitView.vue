<template>
  <div class="flex items-start gap-6">
    <!-- `flex-[3]`/`flex-[2]` reparten después del gap; `min-w-0` deja que la tabla se encoja. -->
    <div class="min-w-0 flex-[3]">
      <!-- Los filtros van sobre la tabla, no sobre el panel: filtran lo listado. -->
      <div v-if="$slots.filters" class="mb-4">
        <slot name="filters" />
      </div>

      <p
        v-if="error"
        class="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600"
      >
        {{ error }}
      </p>

      <div class="rounded-2xl border border-brand-divider bg-white">
        <slot name="table" />
      </div>

      <slot name="footer" />
    </div>

    <!-- Oculto bajo xl: trabajar contra una tabla y un panel es tarea de escritorio. -->
    <aside class="sticky top-6 hidden min-w-0 flex-[2] xl:block">
      <slot name="panel" />
    </aside>
  </div>
</template>

<script lang="ts" setup>
/**
 * El reparto 60/40 de las vistas admin: la tabla es el índice y el panel de la
 * derecha muestra la fila elegida. No sabe qué se lista ni qué se hace con eso.
 */
defineProps<{ error?: string | null }>();

defineSlots<{
  filters?: () => unknown;
  table: () => unknown;
  footer?: () => unknown;
  panel?: () => unknown;
}>();
</script>
