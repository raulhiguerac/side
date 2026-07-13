<template>
  <div class="max-w-2xl mx-auto px-6 py-10">
    <StepImagenes v-model="files" />
    <pre class="mt-6 text-xs text-brand-muted">{{
      files.map((f) => f.name)
    }}</pre>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import StepImagenes from "@/components/properties/create/StepImagenes.vue";

const files = ref<File[]>([]);
</script>
