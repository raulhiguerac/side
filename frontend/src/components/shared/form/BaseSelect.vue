<template>
  <select
    v-model="model"
    :class="[FIELD_BASE, FIELD_SIZE[size], fieldBorder(invalid)]"
  >
    <slot />
  </select>
</template>

<script lang="ts" setup>
import type { FieldSize } from "@/types/shared/ui";
import {
  FIELD_BASE,
  FIELD_SIZE,
  fieldBorder,
} from "@/components/shared/form/fieldClasses";

// v-model nativo adentro: reaplica el valor cuando las opciones llegan después (async).
withDefaults(defineProps<{ size?: FieldSize; invalid?: boolean }>(), {
  size: "md",
  invalid: false,
});

const model = defineModel<string | number | null>();
</script>
