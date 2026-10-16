<template>
  <div class="space-y-3">
    <div>
      <label :class="LABEL_CLASSES" :for="`${idPrefix}-name`">Nombre</label>
      <input
        :id="`${idPrefix}-name`"
        v-model="name"
        type="text"
        maxlength="100"
        placeholder="Obligatorio"
        :disabled="disabled"
        :class="INPUT_CLASSES"
      />
    </div>

    <div class="grid grid-cols-2 gap-3">
      <div>
        <label :class="LABEL_CLASSES" :for="`${idPrefix}-official`">
          Nombre oficial
        </label>
        <input
          :id="`${idPrefix}-official`"
          v-model="officialName"
          type="text"
          placeholder="Opcional"
          :disabled="disabled"
          :class="INPUT_CLASSES"
        />
      </div>
      <div>
        <label :class="LABEL_CLASSES" :for="`${idPrefix}-native`">
          Nombre nativo
        </label>
        <input
          :id="`${idPrefix}-native`"
          v-model="nativeName"
          type="text"
          maxlength="100"
          placeholder="Opcional"
          :disabled="disabled"
          :class="INPUT_CLASSES"
        />
      </div>
    </div>

    <div class="grid grid-cols-3 gap-3">
      <div>
        <label :class="LABEL_CLASSES" :for="`${idPrefix}-phone`">
          Prefijo
        </label>
        <input
          :id="`${idPrefix}-phone`"
          v-model="phoneCode"
          type="text"
          maxlength="8"
          placeholder="+57"
          :disabled="disabled"
          :class="INPUT_CLASSES"
        />
      </div>
      <div>
        <label :class="LABEL_CLASSES" :for="`${idPrefix}-currency`">
          Moneda
        </label>
        <input
          :id="`${idPrefix}-currency`"
          v-model="currencyCode"
          type="text"
          maxlength="3"
          placeholder="COP"
          :disabled="disabled"
          :class="[INPUT_CLASSES, 'uppercase']"
        />
      </div>
      <div>
        <label :class="LABEL_CLASSES" :for="`${idPrefix}-locale`">
          Idioma
        </label>
        <input
          :id="`${idPrefix}-locale`"
          v-model="defaultLocale"
          type="text"
          maxlength="10"
          placeholder="es"
          :disabled="disabled"
          :class="INPUT_CLASSES"
        />
      </div>
    </div>

    <div>
      <label :class="LABEL_CLASSES" :for="`${idPrefix}-timezone`">
        Zona horaria
      </label>
      <input
        :id="`${idPrefix}-timezone`"
        v-model="defaultTimezone"
        type="text"
        maxlength="64"
        placeholder="America/Bogota"
        :disabled="disabled"
        :class="INPUT_CLASSES"
      />
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
        class="accent-brand-primary h-4 w-4"
      />
      Soportado por la plataforma
    </label>
  </div>
</template>

<script lang="ts" setup>
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

const LABEL_CLASSES = "text-brand-text mb-1 block text-sm font-medium";
const INPUT_CLASSES =
  "border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm transition-colors focus:outline-none disabled:opacity-50";
</script>
