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
    <div class="relative custom-wrapper">
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
        <button
          @click="removeCity(id)"
          type="button"
          class="ml-1 hover:text-red-500 font-bold"
        >
          ×
        </button>
      </span>
    </div>
    <div class="flex justify-center mt-6">
      <button
        @click="handleNext"
        type="button"
        class="w-3/5 bg-brand-primary text-white text-sm font-semibold py-2.5 rounded-full hover:bg-green-500 hover:shadow-md transition-all duration-200"
      >
        Continuar
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import Multiselect from "@vueform/multiselect";
import { useOnboarding } from "@/composables/onboarding/useOnboarding";
import { load, cities } from "@/composables/catalog/useCities";
import { useCityMultiselect } from "@/composables/shared/useMultiselect";

const { saveCity } = useOnboarding();
const { selected, removeCity } = useCityMultiselect();

onMounted(() => load());

async function handleNext() {
  const localities = selected.value.map((id) => ({
    id,
    name: cities.value.get(id) ?? "",
  }));
  await saveCity(localities);
}
</script>

<style>
.custom-wrapper {
  --ms-radius: 0.75rem;
  --ms-border-color: #d1d5db;
  --ms-border-color-active: #22c55e;
  --ms-ring-color: #dcfce7;
  --ms-ring-width: 3px;
  --ms-font-size: 0.875rem;
  --ms-placeholder-color: #9ca3af;
  --ms-option-bg-pointed: #dcfce7;
  --ms-option-color-pointed: #22c55e;
  --ms-option-bg-selected: #22c55e;
  --ms-option-bg-selected-pointed: #16a34a;
  --ms-dropdown-radius: 0.75rem;
  --ms-max-height: 12rem;
}

.custom-wrapper .multiselect-search,
.custom-wrapper .multiselect-placeholder {
  padding-left: 2.25rem;
}

.custom-wrapper .multiselect-tags,
.custom-wrapper .multiselect-tag {
  display: none !important;
}
</style>
