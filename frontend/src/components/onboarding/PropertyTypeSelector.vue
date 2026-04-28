<template>
  <div class="bg-white p-2 w-full max-w-sm mx-auto">
    <div class="text-center mb-3">
      <h4 class="text-brand-text text-sm font-semibold">
        ¿Qué tipo de inmueble te interesa?
      </h4>
    </div>
    <p class="text-brand-muted text-xs mb-3 text-center">
      Selecciona los tipos de propiedad por ciudad.
    </p>

    <!-- Tabs por ciudad -->
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

    <!-- Opciones de tipo de propiedad -->
    <div class="grid grid-cols-2 gap-3 px-2 mb-4">
      <button
        v-for="type in propertyTypes"
        :key="type.value"
        type="button"
        @click="toggleType(type.value)"
        class="flex flex-col items-center gap-1.5 p-5 rounded-lg border transition-all"
        :class="
          isSelected(type.value)
            ? 'bg-brand-primary-light border-brand-primary'
            : 'bg-white border-brand-border hover:border-brand-muted'
        "
      >
        <div
          class="w-8 h-8 rounded-lg flex items-center justify-center"
          :class="isSelected(type.value) ? 'bg-brand-primary' : 'bg-brand-bg'"
        >
          <img :src="type.icon" class="w-4 h-4" :alt="type.label" />
        </div>
        <span
          class="text-xs font-medium"
          :class="
            isSelected(type.value) ? 'text-brand-primary' : 'text-brand-text'
          "
        >
          {{ type.label }}
        </span>
      </button>
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
import { ref, watch } from "vue";
import houseIcon from "@/assets/house.svg";
import apartmentIcon from "@/assets/apartment.svg";

const props = defineProps<{
  cities: { id: string; name: string }[];
}>();

const propertyTypes = [
  { value: "apartment", label: "Apartamento", icon: apartmentIcon },
  { value: "house", label: "Casa", icon: houseIcon },
];

const selections = ref<Record<string, string[]>>({});
const activeTab = ref<string | null>(null);

watch(
  () => props.cities,
  (newCities) => {
    newCities.forEach((city) => {
      if (!selections.value[city.id]) {
        selections.value[city.id] = ["apartment"];
      }
    });
    if (!activeTab.value && newCities.length > 0) {
      activeTab.value = newCities[0].id;
    }
  },
  { immediate: true }
);

function isSelected(type: string) {
  return selections.value[activeTab.value!]?.includes(type) ?? false;
}

function toggleType(type: string) {
  if (!activeTab.value) return;
  const current = selections.value[activeTab.value];
  if (current.includes(type)) {
    selections.value[activeTab.value] = current.filter((t) => t !== type);
  } else {
    current.push(type);
  }
}

async function handleNext() {
  // TODO: reemplazar con endpoint real
  console.log("property type selections:", selections.value);
}
</script>

<style scoped></style>
