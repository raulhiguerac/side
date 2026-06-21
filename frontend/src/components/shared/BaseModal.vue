<template>
  <Transition name="fade">
    <div
      v-if="modelValue"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click.self="$emit('update:modelValue', false)"
    >
      <div :class="['bg-white rounded-lg shadow-xl w-full p-6', sizeClass]">
        <slot />
      </div>
    </div>
  </Transition>
</template>

<script lang="ts" setup>
const { size = "lg" } = defineProps<{
  modelValue: boolean;
  size?: "lg" | "xl" | "3xl";
}>();

const sizeClass = {
  lg: "max-w-lg",
  xl: "max-w-xl",
  "3xl": "max-w-3xl",
}[size];

defineEmits(["update:modelValue"]);
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
