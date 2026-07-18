<template>
  <div
    class="flex justify-between items-center bg-white rounded-2xl border border-brand-divider p-6"
  >
    <button
      @click="emit('back')"
      class="px-3 py-2 text-sm font-medium text-brand-muted hover:text-brand-text transition"
    >
      ← Volver
    </button>
    <PrimaryButton @click="emit('save')" class="px-7 py-2.5">
      <Save class="w-4 h-4" />
      Guardar cambios
    </PrimaryButton>
  </div>
</template>

<script lang="ts" setup>
import { Save } from "@lucide/vue";
import PrimaryButton from "@/components/shared/PrimaryButton.vue";

const emit = defineEmits<{
  (e: "back"): void;
  (e: "save"): void;
}>();
</script>
