<template>
  <BaseModal :model-value="open" @update:model-value="$emit('close')">
    <div class="mb-4 flex items-center gap-4">
      <div
        :class="[
          'flex h-12 w-12 shrink-0 items-center justify-center rounded-xl',
          danger ? 'bg-red-100' : 'bg-brand-primary-light',
        ]"
      >
        <component
          :is="icon"
          :class="['h-6 w-6', danger ? 'text-red-600' : 'text-brand-primary']"
        />
      </div>
      <div class="min-w-0">
        <h3 class="text-brand-text text-lg font-bold">{{ title }}</h3>
        <p v-if="subtitle" class="text-brand-muted truncate text-sm">
          {{ subtitle }}
        </p>
      </div>
    </div>

    <slot />

    <!-- El slot reemplaza el pie: p. ej. el "Listo" tras un bulk. -->
    <slot name="footer">
      <FormMessage v-if="error" variant="error" class="mb-4">
        {{ error }}
      </FormMessage>

      <div class="flex gap-3">
        <button
          type="button"
          :disabled="saving"
          class="text-brand-text hover:bg-brand-bg flex-1 rounded-xl py-3 text-sm font-semibold transition-colors disabled:opacity-50"
          @click="$emit('close')"
        >
          Cancelar
        </button>
        <button
          type="button"
          :disabled="saving || !canSubmit"
          :class="[
            'flex-1 rounded-xl py-3 text-sm font-semibold text-white transition-colors disabled:cursor-not-allowed disabled:opacity-50',
            danger
              ? 'bg-red-500 hover:bg-red-600'
              : 'bg-brand-primary hover:opacity-90',
          ]"
          @click="$emit('submit')"
        >
          {{ saving ? savingLabel : submitLabel }}
        </button>
      </div>
    </slot>
  </BaseModal>
</template>

<script lang="ts" setup>
import type { Component } from "vue";
import BaseModal from "@/components/shared/BaseModal.vue";
import FormMessage from "@/components/shared/FormMessage.vue";

// Cascarón de los modales admin: encabezado, error y Cancelar / acción.
withDefaults(
  defineProps<{
    open: boolean;
    icon: Component;
    title: string;
    subtitle?: string;
    submitLabel: string;
    savingLabel: string;
    saving?: boolean;
    canSubmit?: boolean;
    error?: string | null;
    danger?: boolean;
  }>(),
  { subtitle: undefined, saving: false, canSubmit: true, error: null }
);

defineEmits<{ close: []; submit: [] }>();

defineSlots<{ default?: () => unknown; footer?: () => unknown }>();
</script>
