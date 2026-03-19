<template>
  <div class="bg-white p-2 w-full max-w-sm mx-auto">
    <div class="text-center mb-3">
      <h4 class="text-brand-text text-sm font-semibold">
        ¿En qué barrios te gustaría vivir?
      </h4>
    </div>
    <p class="text-brand-muted text-xs mb-3 text-center">
      Elige hasta 5 barrios por ciudad.
    </p>

    <!-- Tabs -->
    <div class="flex border-b border-brand-divider mb-3">
      <button
        v-for="city in cities"
        :key="city.id"
        type="button"
        @click="activeTab = city.id"
        class="px-3 py-2 text-xs font-semibold transition-all border-b-2 -mb-px"
        :class="
          activeTab === city.id
            ? 'text-brand-primary border-brand-primary'
            : 'text-brand-muted border-transparent hover:text-brand-text'
        "
      >
        {{ city.name }}
      </button>
    </div>

    <!-- Multiselect por tab -->
    <div
      v-for="city in cities"
      :key="city.id"
      v-show="activeTab === city.id"
      class="relative custom-wrapper"
    >
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
        v-model="selectedByCity[city.id]"
        :options="
          city.neighborhoods.map((n) => ({ value: n.id, label: n.name }))
        "
        mode="multiple"
        :searchable="true"
        :max="5"
        :multiple-label="() => ''"
        :close-on-select="true"
        :hide-selected="true"
        placeholder="Busca un barrio..."
      />
    </div>

    <div v-if="allSelected.length" class="flex flex-wrap gap-2 mt-3 mb-2">
      <span
        v-for="item in allSelected"
        :key="item.neighborhoodId"
        class="inline-flex items-center gap-1 bg-brand-primary-light text-brand-primary text-xs font-semibold px-3 py-1.5 rounded-full"
      >
        <span class="text-brand-primary/60 font-normal"
          >{{ item.cityName }} · </span
        >{{ item.neighborhoodName }}
        <button
          type="button"
          @click="removeNeighborhood(item.cityId, item.neighborhoodId)"
          class="ml-1 hover:text-red-500 font-bold"
        >
          ×
        </button>
      </span>
    </div>

    <div class="flex justify-center mt-4">
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
import { ref, computed } from "vue";
import Multiselect from "@vueform/multiselect";

interface Neighborhood {
  id: string;
  name: string;
}

interface CityWithNeighborhoods {
  id: string;
  name: string;
  neighborhoods: Neighborhood[];
}

// TODO: reemplazar con ciudades seleccionadas en el paso anterior
const cities = ref<CityWithNeighborhoods[]>([
  {
    id: "city-bogota",
    name: "Bogotá D.C.",
    neighborhoods: [
      { id: "n-chapinero", name: "Chapinero" },
      { id: "n-usaquen", name: "Usaquén" },
      { id: "n-suba", name: "Suba" },
      { id: "n-kennedy", name: "Kennedy" },
      { id: "n-teusaquillo", name: "Teusaquillo" },
    ],
  },
  {
    id: "city-medellin",
    name: "Medellín",
    neighborhoods: [
      { id: "n-laureles", name: "Laureles" },
      { id: "n-poblado", name: "El Poblado" },
      { id: "n-envigado", name: "Envigado" },
      { id: "n-belen", name: "Belén" },
    ],
  },
]);

const activeTab = ref(cities.value[0]?.id ?? "");
const selectedByCity = ref<Record<string, string[]>>(
  Object.fromEntries(cities.value.map((c) => [c.id, []]))
);

const allSelected = computed(() =>
  cities.value.flatMap((city) =>
    (selectedByCity.value[city.id] ?? []).map((neighborhoodId) => ({
      cityId: city.id,
      cityName: city.name,
      neighborhoodId,
      neighborhoodName:
        city.neighborhoods.find((n) => n.id === neighborhoodId)?.name ?? "",
    }))
  )
);

function removeNeighborhood(cityId: string, neighborhoodId: string) {
  selectedByCity.value[cityId] = selectedByCity.value[cityId].filter(
    (id) => id !== neighborhoodId
  );
}

async function handleNext() {
  // TODO: llamar saveNeighborhoods(allSelected.value)
  console.log("seleccionados:", allSelected.value);
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
