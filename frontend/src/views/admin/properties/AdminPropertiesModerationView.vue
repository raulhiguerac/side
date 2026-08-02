<template>
  <div class="flex items-start gap-6">
    <!-- 60/40 vía `flex-[3]` / `flex-[2]`, que reparten el espacio *después*
         del gap; con `w-3/5` + `w-2/5` la suma daría 100% más el gap y los dos
         hijos tendrían que encogerse para entrar.

         `min-w-0` deja que la tabla se encoja: sin eso el hijo flex toma el
         ancho de su contenido y empuja el panel fuera de la pantalla. -->
    <div class="min-w-0 flex-[3]">
      <p
        v-if="error"
        class="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600"
      >
        {{ error }}
      </p>

      <div class="rounded-2xl border border-brand-divider bg-white">
        <AdminPropertiesTable
          :rows="rows"
          :loading="loading"
          :selected-id="selectedId"
          @row-click="selectedId = $event.id"
        />
      </div>

      <div
        v-if="serverTotal"
        class="mt-6 flex flex-col items-center gap-3 sm:flex-row sm:justify-between"
      >
        <p class="text-brand-muted text-sm">
          Mostrando {{ range.from }}-{{ range.to }} de
          {{ serverTotal.toLocaleString("es-CO") }}
        </p>
        <PaginationArrows
          :has-prev="hasPrev"
          :has-next="hasNext"
          @prev="prev"
          @next="next"
        />
      </div>
    </div>

    <!-- Oculto por debajo de xl: un panel al lado de la tabla no entra en
         pantallas chicas, y moderar es una tarea de escritorio. -->
    <aside class="sticky top-6 hidden min-w-0 flex-[2] xl:block">
      <AdminPropertyPreviewPanel :property-id="selectedId" />
    </aside>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, ref, watch } from "vue";
import PaginationArrows from "@/components/shared/PaginationArrows.vue";
import AdminPropertiesTable from "@/components/admin/properties/AdminPropertiesTable.vue";
import AdminPropertyPreviewPanel from "@/components/admin/properties/AdminPropertyPreviewPanel.vue";
import { useAdminProperties } from "@/composables/admin/useAdminProperties";

const {
  rows,
  hasPrev,
  hasNext,
  serverTotal,
  range,
  loading,
  error,
  load,
  next,
  prev,
} = useAdminProperties();

const selectedId = ref<string | null>(null);

/**
 * El panel arranca con la primera fila ya elegida en vez de vacío. Se vigila
 * `rows` y no solo la carga inicial porque al paginar cambia la página entera:
 * la selección anterior deja de estar visible y quedaría marcada una fila que
 * no se ve. Si la seleccionada sigue en la página, no se toca.
 */
watch(
  rows,
  (list) => {
    if (!list.length) {
      selectedId.value = null;
      return;
    }
    if (!list.some((row) => row.id === selectedId.value)) {
      selectedId.value = list[0].id;
    }
  },
  { immediate: true }
);

onMounted(load);
</script>
