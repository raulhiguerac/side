<template>
  <div class="min-h-screen bg-gray-100 flex items-center justify-center p-6">
    <PropertyTypeSelector :cities="mockCities" />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import PropertyTypeSelector from "@/components/onboarding/PropertyTypeSelector.vue";

const mockCities = ref([
  { id: "1", name: "Bogotá" },
  { id: "2", name: "Medellín" },
]);
</script>
