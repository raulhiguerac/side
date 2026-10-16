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

    <div v-if="isLoading" class="flex justify-center items-center py-10">
      <BaseSpinner class="h-6 w-6 text-brand-primary" />
    </div>

    <template v-else>
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
        class="relative brand-multiselect"
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
          <IconButton
            label="Quitar barrio"
            size="xs"
            danger
            @click="removeNeighborhood(item.cityId, item.neighborhoodId)"
            class="ml-1"
          >
            ×
          </IconButton>
        </span>
      </div>

      <div class="flex justify-center mt-4">
        <BaseButton
          size="lg"
          :loading="saving"
          @click="handleNext"
          :disabled="saving"
          class="w-3/5"
        >
          {{ saving ? "Guardando..." : "Continuar" }}
        </BaseButton>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import BaseButton from "@/components/shared/BaseButton.vue";
import IconButton from "@/components/shared/IconButton.vue";
import { ref, onMounted } from "vue";
import Multiselect from "@vueform/multiselect";
import { useLocalitiesWithNames } from "@/composables/catalog/useLocalitiesWithNames";
import { useNeighborhoodMultiselect } from "@/composables/shared/useMultiselect";
import BaseSpinner from "@/components/shared/BaseSpinner.vue";
import type { NeighborhoodSelection } from "@/types/users/interests";

defineProps<{ saving?: boolean }>();
const emit = defineEmits<{ submit: [localities: NeighborhoodSelection[]] }>();
const { load: loadLocalities } = useLocalitiesWithNames();
const { cities, selectedByCity, allSelected, removeNeighborhood, load } =
  useNeighborhoodMultiselect();

const activeTab = ref("");
const isLoading = ref(true);

onMounted(async () => {
  const enrichedLocalities = await loadLocalities();
  await load(enrichedLocalities);
  activeTab.value = cities.value[0]?.id ?? "";
  isLoading.value = false;
});

function handleNext() {
  const payload = cities.value.map((city) => ({
    locality_id: city.id,
    neighborhoods: Object.fromEntries(
      (selectedByCity.value[city.id] ?? []).map((neighborhoodId, index) => [
        index + 1,
        neighborhoodId,
      ])
    ),
  }));
  emit("submit", payload);
}
</script>
