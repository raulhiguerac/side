<template>
  <BaseModal :model-value="open" @update:model-value="$emit('close')">
    <div class="mb-4 flex items-center gap-4">
      <div
        :class="[
          'flex h-12 w-12 shrink-0 items-center justify-center rounded-xl',
          danger ? 'bg-brand-danger-light' : 'bg-brand-primary-light',
        ]"
      >
        <component
          :is="icon"
          :class="[
            'h-6 w-6',
            danger ? 'text-brand-danger' : 'text-brand-primary',
          ]"
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
        <BaseButton
          variant="ghost"
          size="lg"
          :disabled="saving"
          @click="$emit('close')"
          class="flex-1"
        >
          Cancelar
        </BaseButton>
        <BaseButton
          :variant="danger ? 'danger' : 'primary'"
          size="lg"
          :disabled="saving || !canSubmit"
          @click="$emit('submit')"
          class="flex-1"
        >
          {{ saving ? savingLabel : submitLabel }}
        </BaseButton>
      </div>
    </slot>
  </BaseModal>
</template>

<script lang="ts" setup>
import BaseButton from "@/components/shared/BaseButton.vue";
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
