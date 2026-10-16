<template>
  <input
    :type="type"
    :value="model"
    :class="[FIELD_BASE, FIELD_SIZE[size], fieldBorder(invalid)]"
    @input="onInput"
  />
</template>

<script lang="ts" setup>
import { looseToNumber } from "@/utils/number";
import type { FieldSize } from "@/types/shared/ui";
import {
  FIELD_BASE,
  FIELD_SIZE,
  fieldBorder,
} from "@/components/shared/form/fieldClasses";

// Sin la directiva v-model adentro: así también sirve con `:value` + `@input`, que pisan por fallthrough.
const props = withDefaults(
  defineProps<{ size?: FieldSize; invalid?: boolean; type?: string }>(),
  { size: "md", invalid: false, type: "text" }
);

const model = defineModel<string | number | null>();

function onInput(event: Event) {
  if (!(event.target instanceof HTMLInputElement)) return;
  const { value } = event.target;
  model.value = props.type === "number" ? looseToNumber(value) : value;
}
</script>
