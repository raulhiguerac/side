<template>
  <div class="space-y-3">
    <div>
      <FormField label="Nombre" :input-id="`${idPrefix}-name`">
        <BaseInput
          :id="`${idPrefix}-name`"
          v-model="name"
          type="text"
          maxlength="100"
          placeholder="Obligatorio"
          :disabled="disabled"
        />
      </FormField>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <div>
        <FormField label="Nombre oficial" :input-id="`${idPrefix}-official`">
          <BaseInput
            :id="`${idPrefix}-official`"
            v-model="officialName"
            type="text"
            placeholder="Opcional"
            :disabled="disabled"
          />
        </FormField>
      </div>
      <div>
        <FormField label="Nombre nativo" :input-id="`${idPrefix}-native`">
          <BaseInput
            :id="`${idPrefix}-native`"
            v-model="nativeName"
            type="text"
            maxlength="100"
            placeholder="Opcional"
            :disabled="disabled"
          />
        </FormField>
      </div>
    </div>

    <div class="grid grid-cols-3 gap-3">
      <div>
        <FormField label="Prefijo" :input-id="`${idPrefix}-phone`">
          <BaseInput
            :id="`${idPrefix}-phone`"
            v-model="phoneCode"
            type="text"
            maxlength="8"
            placeholder="+57"
            :disabled="disabled"
          />
        </FormField>
      </div>
      <div>
        <FormField label="Moneda" :input-id="`${idPrefix}-currency`">
          <BaseInput
            :id="`${idPrefix}-currency`"
            v-model="currencyCode"
            type="text"
            maxlength="3"
            placeholder="COP"
            :disabled="disabled"
            class="uppercase"
          />
        </FormField>
      </div>
      <div>
        <FormField label="Idioma" :input-id="`${idPrefix}-locale`">
          <BaseInput
            :id="`${idPrefix}-locale`"
            v-model="defaultLocale"
            type="text"
            maxlength="10"
            placeholder="es"
            :disabled="disabled"
          />
        </FormField>
      </div>
    </div>

    <div>
      <FormField label="Zona horaria" :input-id="`${idPrefix}-timezone`">
        <BaseInput
          :id="`${idPrefix}-timezone`"
          v-model="defaultTimezone"
          type="text"
          maxlength="64"
          placeholder="America/Bogota"
          :disabled="disabled"
        />
      </FormField>
    </div>

    <label
      class="text-brand-text flex items-center gap-2 text-sm font-medium"
      :for="`${idPrefix}-supported`"
    >
      <input
        :id="`${idPrefix}-supported`"
        v-model="isSupported"
        type="checkbox"
        :disabled="disabled"
        class="accent-brand-primary h-4 w-4 appearance-auto"
      />
      Soportado por la plataforma
    </label>
  </div>
</template>

<script lang="ts" setup>
import FormField from "@/components/shared/form/FormField.vue";
import BaseInput from "@/components/shared/form/BaseInput.vue";
// Campos editables, compartidos por crear y editar; los códigos ISO van en el modal de crear.
defineProps<{ idPrefix: string; disabled?: boolean }>();

const name = defineModel<string>("name", { required: true });
const officialName = defineModel<string>("officialName", { required: true });
const nativeName = defineModel<string>("nativeName", { required: true });
const phoneCode = defineModel<string>("phoneCode", { required: true });
const currencyCode = defineModel<string>("currencyCode", { required: true });
const defaultLocale = defineModel<string>("defaultLocale", { required: true });
const defaultTimezone = defineModel<string>("defaultTimezone", {
  required: true,
});
const isSupported = defineModel<boolean>("isSupported", { required: true });
</script>
