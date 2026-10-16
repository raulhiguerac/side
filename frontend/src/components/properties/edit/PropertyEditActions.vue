<template>
  <div
    class="flex justify-between items-center bg-white rounded-2xl border border-brand-divider p-6"
  >
    <BaseButton variant="ghost" @click="emit('back')"> ← Volver </BaseButton>
    <BaseButton @click="emit('save')">
      <Save class="w-4 h-4" />
      Guardar cambios
    </BaseButton>
  </div>
</template>

<script lang="ts" setup>
import BaseButton from "@/components/shared/BaseButton.vue";
import { Save } from "@lucide/vue";

const emit = defineEmits<{
  (e: "back"): void;
  (e: "save"): void;
}>();
</script>
