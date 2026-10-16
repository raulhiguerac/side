<template>
  <div class="bg-white p-2 w-full max-w-sm mx-auto">
    <div class="text-center mb-3">
      <h4 class="text-brand-text text-sm font-semibold">
        ¿Dónde te gustaría buscar?
      </h4>
    </div>
    <p class="text-brand-muted text-xs mb-3 text-center">
      Elige hasta 3 ciudades para personalizar tu experiencia.
    </p>
    <div class="relative brand-multiselect">
      <div
        class="absolute left-3 top-1/2 -translate-y-1/2 z-10 pointer-events-none text-brand-placeholder"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z"
          />
        </svg>
      </div>

      <Multiselect
        v-model="selected"
        :options="
          [...cities.entries()].map(([id, name]) => ({
            value: id,
            label: name,
          }))
        "
        mode="multiple"
        :searchable="true"
        :hide-selected="true"
        :max="3"
        :multiple-label="() => ''"
        :close-on-select="true"
        placeholder="Selecciona una o más ciudades"
      />
    </div>

    <div v-if="selected.length" class="flex flex-wrap gap-2 mt-2 mb-4">
      <span
        v-for="id in selected"
        :key="id"
        class="inline-flex items-center gap-1 bg-brand-primary-light text-brand-primary text-xs font-semibold px-3 py-1.5 rounded-full"
      >
        {{ cities.get(id) }}
        <IconButton
          label="Quitar ciudad"
          size="xs"
          danger
          @click="removeCity(id)"
          class="ml-1"
        >
          ×
        </IconButton>
      </span>
    </div>
    <div class="flex justify-center mt-6">
      <BaseButton size="lg" @click="handleNext" class="w-3/5">
        Continuar
      </BaseButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import BaseButton from "@/components/shared/BaseButton.vue";
import IconButton from "@/components/shared/IconButton.vue";
import { onMounted } from "vue";
import Multiselect from "@vueform/multiselect";
import { load, cities } from "@/composables/catalog/useCities";
import { useCityMultiselect } from "@/composables/shared/useMultiselect";
import type { CatalogItem } from "@/types/catalog/base";

const emit = defineEmits<{ submit: [localities: CatalogItem[]] }>();
const { selected, removeCity } = useCityMultiselect();

onMounted(() => load());

function handleNext() {
  const localities = selected.value.map((id) => ({
    id,
    name: cities.value.get(id) ?? "",
  }));
  emit("submit", localities);
}
</script>
