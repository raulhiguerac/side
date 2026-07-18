<template>
  <div class="flex flex-col gap-6">
    <!-- Preferences -->
    <div>
      <h2 class="text-base font-semibold text-brand-text mb-4">Preferencias</h2>

      <div class="flex flex-col gap-4">
        <!-- city_ids -->
        <div>
          <label
            class="text-xs font-medium text-brand-muted uppercase tracking-wide mb-1.5 block"
          >
            Ciudad
          </label>
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
          <div v-if="selected.length" class="flex flex-wrap gap-2 mt-2">
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
        </div>
        <!-- neighborhood_ids -->
        <div>
          <label
            class="text-xs font-medium text-brand-muted uppercase tracking-wide mb-1.5 block"
          >
            Barrio
          </label>
          <Multiselect
            v-model="selectedNeighborhoods"
            :options="allNeighborhoodOptions"
            mode="multiple"
            :searchable="true"
            :hide-selected="true"
            :multiple-label="() => ''"
            :close-on-select="true"
            placeholder="Selecciona uno o más barrios"
            :disabled="!allNeighborhoodOptions.length"
          />
          <div
            v-if="selectedNeighborhoods.length"
            class="flex flex-wrap gap-2 mt-2"
          >
            <span
              v-for="id in selectedNeighborhoods"
              :key="id"
              class="inline-flex items-center gap-1 bg-brand-primary-light text-brand-primary text-xs font-semibold px-3 py-1.5 rounded-full"
            >
              {{ allNeighborhoodOptions.find((o) => o.value === id)?.label }}
              <button
                type="button"
                @click="
                  selectedNeighborhoods = selectedNeighborhoods.filter(
                    (n) => n !== id
                  )
                "
                class="ml-1 hover:text-red-500 font-bold"
              >
                ×
              </button>
            </span>
          </div>
        </div>

        <!-- property_types -->
        <div>
          <label
            class="text-xs font-medium text-brand-muted uppercase tracking-wide mb-2 block"
          >
            Tipo de propiedad
          </label>
          <div class="flex gap-2">
            <button
              @click="toggleType('house')"
              :class="
                selectedTypes.includes('house')
                  ? 'bg-brand-primary border-brand-primary text-white'
                  : 'border-brand-border text-brand-text hover:border-brand-primary'
              "
              class="flex-1 py-2 rounded-xl border text-sm transition-colors"
            >
              Casa
            </button>
            <button
              @click="toggleType('apartment')"
              :class="
                selectedTypes.includes('apartment')
                  ? 'bg-brand-primary border-brand-primary text-white'
                  : 'border-brand-border text-brand-text hover:border-brand-primary'
              "
              class="flex-1 py-2 rounded-xl border text-sm transition-colors"
            >
              Apartamento
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="border-t border-brand-divider pt-6">
      <h3 class="text-base font-semibold text-brand-text mb-4">Filtros</h3>

      <div class="flex flex-col gap-4">
        <!-- price range -->
        <div>
          <label
            class="text-xs font-medium text-brand-muted uppercase tracking-wide mb-1.5 block"
          >
            Precio
          </label>
          <div class="flex gap-2">
            <input
              v-model.number="filters.min_price"
              type="number"
              placeholder="Mín"
              class="w-1/2 px-3 py-2 text-sm rounded-xl border border-brand-border focus:outline-none focus:border-brand-primary"
            />
            <input
              v-model.number="filters.max_price"
              type="number"
              placeholder="Máx"
              class="w-1/2 px-3 py-2 text-sm rounded-xl border border-brand-border focus:outline-none focus:border-brand-primary"
            />
          </div>
        </div>

        <!-- area range -->
        <div>
          <label
            class="text-xs font-medium text-brand-muted uppercase tracking-wide mb-1.5 block"
          >
            Área (m²)
          </label>
          <div class="flex gap-2">
            <input
              v-model.number="filters.min_area_m2"
              type="number"
              placeholder="Mín"
              class="w-1/2 px-3 py-2 text-sm rounded-xl border border-brand-border focus:outline-none focus:border-brand-primary"
            />
            <input
              v-model.number="filters.max_area_m2"
              type="number"
              placeholder="Máx"
              class="w-1/2 px-3 py-2 text-sm rounded-xl border border-brand-border focus:outline-none focus:border-brand-primary"
            />
          </div>
        </div>

        <!-- bedrooms -->
        <div>
          <label
            class="text-xs font-medium text-brand-muted uppercase tracking-wide mb-1.5 block"
          >
            Habitaciones
          </label>
          <input
            v-model.number="filters.bedrooms"
            type="number"
            placeholder="Ej. 3"
            min="1"
            class="w-full px-3 py-2 text-sm rounded-xl border border-brand-border focus:outline-none focus:border-brand-primary"
          />
        </div>

        <!-- min_bathrooms -->
        <div>
          <label
            class="text-xs font-medium text-brand-muted uppercase tracking-wide mb-1.5 block"
          >
            Baños (mín)
          </label>
          <input
            v-model.number="filters.min_bathrooms"
            type="number"
            placeholder="Ej. 2"
            min="1"
            class="w-full px-3 py-2 text-sm rounded-xl border border-brand-border focus:outline-none focus:border-brand-primary"
          />
        </div>

        <!-- apply button -->
        <button
          @click="onSubmit"
          class="w-full mt-2 py-2.5 rounded-xl bg-brand-primary text-white text-sm font-semibold hover:bg-green-600 transition-colors"
        >
          Aplicar filtros
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, ref, watch } from "vue";
import Multiselect from "@vueform/multiselect";
import { load, cities } from "@/composables/catalog/useCities";
import {
  useCityMultiselect,
  useNeighborhoodMultiselect,
} from "@/composables/shared/useMultiselect";
import { FeedPreferences, FeedFilters } from "@/types/feed";

const { selected, removeCity } = useCityMultiselect();
const { allNeighborhoodOptions, load: loadNeighborhoods } =
  useNeighborhoodMultiselect();

const filters = ref<FeedFilters>({});
const selectedTypes = ref<Array<string>>([]);
const selectedNeighborhoods = ref<string[]>([]);

const emit = defineEmits<{
  submit: [
    data: {
      preferences: FeedPreferences;
      filters: FeedFilters;
    }
  ];
}>();

onMounted(() => load());

watch(selected, async (cityIds) => {
  const localities = cityIds.map((id) => ({
    id,
    name: cities.value.get(id) ?? "",
  }));
  selectedNeighborhoods.value = [];
  await loadNeighborhoods(localities);
});

function toggleType(element: string) {
  if (selectedTypes.value.includes(element)) {
    selectedTypes.value = selectedTypes.value.filter(
      (active) => active !== element
    );
  } else {
    selectedTypes.value.push(element);
  }
}

function onSubmit() {
  emit("submit", {
    preferences: {
      city_ids: selected.value,
      neighborhood_ids: selectedNeighborhoods.value,
      property_types: selectedTypes.value,
    },
    filters: filters.value,
  });
}
</script>
