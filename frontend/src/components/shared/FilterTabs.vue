<template>
  <div class="flex gap-2 mb-6 overflow-x-auto pb-2">
    <button
      v-for="tab in tabs"
      :key="tab.value"
      @click="$emit('update:modelValue', tab.value)"
      class="px-4 py-2 rounded-lg text-sm font-medium transition-all flex-shrink-0"
      :class="
        modelValue === tab.value
          ? 'bg-brand-primary text-white'
          : 'bg-white text-brand-text hover:bg-brand-bg'
      "
    >
      {{ tab.label }}
      <span
        v-if="getCount"
        class="ml-1.5 px-2 py-0.5 rounded-full text-xs"
        :class="
          modelValue === tab.value
            ? 'bg-white/20 text-white'
            : 'bg-brand-bg text-brand-muted'
        "
      >
        {{ getCount(tab.value) }}
      </span>
    </button>
  </div>
</template>

<script lang="ts" setup>
defineProps<{
  tabs: { label: string; value: string }[];
  modelValue: string;
  getCount?: (value: string) => number;
}>();

defineEmits<{
  (e: "update:modelValue", value: string): void;
}>();
</script>
