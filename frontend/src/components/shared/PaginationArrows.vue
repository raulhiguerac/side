<template>
  <div class="flex items-center justify-center gap-3">
    <button
      :disabled="!hasPrev"
      @click="$emit('prev')"
      class="flex items-center gap-1 px-4 py-2 rounded-xl border border-brand-border text-sm font-medium transition"
      :class="
        hasPrev
          ? 'bg-brand-primary text-white hover:bg-green-600 cursor-pointer'
          : 'opacity-40 cursor-not-allowed'
      "
    >
      <svg
        class="w-4 h-4"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M15 19l-7-7 7-7"
        />
      </svg>
      Anterior
    </button>
    <button
      :disabled="!hasNext"
      @click="$emit('next')"
      class="flex items-center gap-1 px-4 py-2 rounded-xl border border-brand-border text-sm font-medium transition"
      :class="
        hasNext
          ? 'bg-brand-primary text-white hover:bg-green-600 cursor-pointer'
          : 'opacity-40 cursor-not-allowed'
      "
    >
      Siguiente
      <svg
        class="w-4 h-4"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
      </svg>
    </button>
  </div>
</template>

<script lang="ts" setup>
defineProps<{
  hasPrev: boolean;
  hasNext: boolean;
}>();

defineEmits<{
  (e: "prev"): void;
  (e: "next"): void;
}>();
</script>
