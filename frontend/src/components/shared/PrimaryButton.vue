<template>
  <button
    :disabled="disabled"
    class="flex items-center justify-center gap-2 rounded-xl text-white text-sm font-bold transition-all duration-200 hover:-translate-y-0.5 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:translate-y-0"
    style="
      background: linear-gradient(90deg, #22c55e, #16a34a);
      box-shadow: 0 8px 24px rgba(34, 197, 94, 0.35);
    "
  >
    <slot />
  </button>
</template>

<script lang="ts" setup>
defineProps<{
  disabled?: boolean;
}>();
</script>
