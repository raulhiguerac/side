<template>
  <div class="space-y-3">
    <div>
      <label :class="LABEL_CLASSES" :for="`${idPrefix}-name`">Nombre</label>
      <input
        :id="`${idPrefix}-name`"
        v-model="name"
        type="text"
        maxlength="150"
        placeholder="Obligatorio"
        :disabled="disabled"
        :class="INPUT_CLASSES"
      />
    </div>

    <div class="grid grid-cols-2 gap-3">
      <div>
        <label :class="LABEL_CLASSES" :for="`${idPrefix}-type`">Tipo</label>
        <input
          :id="`${idPrefix}-type`"
          v-model="typeName"
          type="text"
          maxlength="50"
          placeholder="Departamento, Estado…"
          :disabled="disabled"
          :class="INPUT_CLASSES"
        />
      </div>
      <div>
        <label :class="LABEL_CLASSES" :for="`${idPrefix}-iso`">
          ISO 3166-2
        </label>
        <input
          :id="`${idPrefix}-iso`"
          v-model="isoCode"
          type="text"
          maxlength="10"
          placeholder="Opcional, p. ej. CO-CUN"
          :disabled="disabled"
          :class="INPUT_CLASSES"
        />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
// Campos editables, compartidos por crear y editar; código y país van en el modal de crear.
defineProps<{ idPrefix: string; disabled?: boolean }>();

const name = defineModel<string>("name", { required: true });
const typeName = defineModel<string>("typeName", { required: true });
const isoCode = defineModel<string>("isoCode", { required: true });

const LABEL_CLASSES = "text-brand-text mb-1 block text-sm font-medium";
const INPUT_CLASSES =
  "border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm transition-colors focus:outline-none disabled:opacity-50";
</script>
