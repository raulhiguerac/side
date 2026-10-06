<template>
  <div class="grid justify-center gap-2" :style="gridStyle">
    <button
      v-for="action in actions"
      :key="action.key"
      type="button"
      :title="action.label"
      :class="[
        'flex min-w-0 items-center justify-center gap-2 rounded-xl border px-3 py-2 text-sm font-medium transition-colors',
        VARIANT_CLASSES[action.variant ?? 'default'],
      ]"
      @click="$emit('action', action.key)"
    >
      <component :is="action.icon" class="h-4 w-4 shrink-0" />
      <span class="truncate">{{ action.label }}</span>
    </button>
  </div>
</template>

<script lang="ts" setup generic="K extends string">
import { computed } from "vue";
import type { AdminAction, AdminActionVariant } from "@/types/admin/actions";

const props = defineProps<{ actions: readonly AdminAction<K>[] }>();

defineEmits<{ action: [key: K] }>();

// Columnas de 1/3 centradas; el gap de 0.5rem es el gap-2.
const gridStyle = computed(() => {
  const tracks = Math.min(props.actions.length, 3);
  return { gridTemplateColumns: `repeat(${tracks}, calc((100% - 1rem) / 3))` };
});

const VARIANT_CLASSES: Record<AdminActionVariant, string> = {
  default: "border-brand-divider text-brand-text hover:bg-brand-bg",
  primary:
    "border-brand-primary bg-brand-primary text-white hover:bg-green-600",
  danger: "border-red-200 text-red-600 hover:bg-red-50",
};
</script>
