<template>
  <div class="grid justify-center gap-2" :style="gridStyle">
    <BaseButton
      v-for="action in actions"
      :key="action.key"
      :variant="BUTTON_VARIANTS[action.variant ?? 'default']"
      :title="action.label"
      @click="$emit('action', action.key)"
      class="min-w-0"
    >
      <component :is="action.icon" class="h-4 w-4 shrink-0" />
      <span class="truncate">{{ action.label }}</span>
    </BaseButton>
  </div>
</template>

<script lang="ts" setup generic="K extends string">
import BaseButton from "@/components/shared/BaseButton.vue";
import { computed } from "vue";
import type { AdminAction, AdminActionVariant } from "@/types/admin/actions";
import type { ButtonVariant } from "@/types/shared/ui";

const props = defineProps<{ actions: readonly AdminAction<K>[] }>();

defineEmits<{ action: [key: K] }>();

// Columnas de 1/3 centradas; el gap de 0.5rem es el gap-2.
const gridStyle = computed(() => {
  const tracks = Math.min(props.actions.length, 3);
  return { gridTemplateColumns: `repeat(${tracks}, calc((100% - 1rem) / 3))` };
});

const BUTTON_VARIANTS: Record<AdminActionVariant, ButtonVariant> = {
  default: "secondary",
  primary: "primary",
  danger: "danger-soft",
};
</script>
