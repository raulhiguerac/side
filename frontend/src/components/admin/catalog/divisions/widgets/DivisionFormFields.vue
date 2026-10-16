<template>
  <div class="space-y-3">
    <div>
      <FormField label="Nombre" :input-id="`${idPrefix}-name`">
        <BaseInput
          :id="`${idPrefix}-name`"
          v-model="name"
          type="text"
          maxlength="150"
          placeholder="Obligatorio"
          :disabled="disabled"
        />
      </FormField>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <div>
        <FormField label="Tipo" :input-id="`${idPrefix}-type`">
          <BaseInput
            :id="`${idPrefix}-type`"
            v-model="typeName"
            type="text"
            maxlength="50"
            placeholder="Departamento, Estado…"
            :disabled="disabled"
          />
        </FormField>
      </div>
      <div>
        <FormField label="ISO 3166-2" :input-id="`${idPrefix}-iso`">
          <BaseInput
            :id="`${idPrefix}-iso`"
            v-model="isoCode"
            type="text"
            maxlength="10"
            placeholder="Opcional, p. ej. CO-CUN"
            :disabled="disabled"
          />
        </FormField>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import FormField from "@/components/shared/form/FormField.vue";
import BaseInput from "@/components/shared/form/BaseInput.vue";
// Campos editables, compartidos por crear y editar; código y país van en el modal de crear.
defineProps<{ idPrefix: string; disabled?: boolean }>();

const name = defineModel<string>("name", { required: true });
const typeName = defineModel<string>("typeName", { required: true });
const isoCode = defineModel<string>("isoCode", { required: true });
</script>
