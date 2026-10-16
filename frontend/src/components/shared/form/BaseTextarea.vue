<template>
  <textarea
    :value="model ?? ''"
    :class="[FIELD_BASE, 'resize-none px-3 py-2', fieldBorder(invalid)]"
    @input="onInput"
  />
</template>

<script lang="ts" setup>
import { FIELD_BASE, fieldBorder } from "@/components/shared/form/fieldClasses";

withDefaults(defineProps<{ invalid?: boolean }>(), { invalid: false });

const model = defineModel<string | null>();

function onInput(event: Event) {
  if (event.target instanceof HTMLTextAreaElement)
    model.value = event.target.value;
}
</script>
