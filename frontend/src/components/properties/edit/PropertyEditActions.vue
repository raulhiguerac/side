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
    <button
      @click="emit('save')"
      class="flex items-center gap-2 px-7 py-2.5 rounded-xl text-white text-sm font-bold transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg"
      style="
        background: linear-gradient(90deg, #22c55e, #16a34a);
        box-shadow: 0 8px 24px rgba(34, 197, 94, 0.35);
      "
    >
      <Save class="w-4 h-4" />
      Guardar cambios
    </button>
  </div>
</template>

<script lang="ts" setup>
import { Save } from "@lucide/vue";

const emit = defineEmits<{
  (e: "back"): void;
  (e: "save"): void;
}>();
</script>
