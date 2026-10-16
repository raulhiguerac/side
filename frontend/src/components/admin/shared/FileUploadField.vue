<template>
  <div>
    <ul
      v-if="requirements.length"
      class="bg-brand-bg mb-4 space-y-2 rounded-xl p-4 text-sm"
    >
      <li
        v-for="requirement in requirements"
        :key="requirement.text"
        class="flex items-start gap-2"
      >
        <Check
          v-if="requirement.accepted"
          class="text-brand-primary mt-0.5 h-4 w-4 shrink-0"
        />
        <X v-else class="mt-0.5 h-4 w-4 shrink-0 text-brand-danger" />
        <span
          :class="requirement.accepted ? 'text-brand-text' : 'text-brand-muted'"
        >
          {{ requirement.text }}
        </span>
      </li>
    </ul>

    <input
      type="file"
      :accept="extensions.join(',')"
      :disabled="disabled"
      class="text-brand-muted block w-full text-sm"
      @change="onChange"
    />
    <p v-if="localError" class="mt-2 text-xs text-brand-danger">
      {{ localError }}
    </p>
  </div>
</template>

<script lang="ts" setup>
import { ref } from "vue";
import { Check, X } from "@lucide/vue";
import type { FileRequirement } from "@/types/shared/ui";

// Valida extensión y tamaño antes de subir; el backend vuelve a validar.
const props = withDefaults(
  defineProps<{
    extensions: readonly string[];
    maxSizeMb: number;
    requirements?: readonly FileRequirement[];
    disabled?: boolean;
  }>(),
  { requirements: () => [], disabled: false }
);

const file = defineModel<File | null>({ default: null });

const localError = ref<string | null>(null);

function rejection(candidate: File): string | null {
  const name = candidate.name.toLowerCase();
  if (!props.extensions.some((ext) => name.endsWith(ext)))
    return `Solo se aceptan archivos ${props.extensions.join(", ")}.`;
  if (candidate.size > props.maxSizeMb * 1024 * 1024)
    return `El archivo supera los ${props.maxSizeMb} MB.`;
  return null;
}

function onChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const candidate = input.files?.[0] ?? null;
  localError.value = candidate ? rejection(candidate) : null;
  file.value = candidate && !localError.value ? candidate : null;
}
</script>
