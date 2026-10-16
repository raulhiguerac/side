<template>
  <div class="relative">
    <BaseInput
      v-model="model"
      v-bind="$attrs"
      :type="visible ? 'text' : 'password'"
      :size="size"
      :invalid="invalid"
      :class="size === 'lg' ? 'pr-12' : 'pr-10'"
    />
    <IconButton
      :label="visible ? 'Ocultar contraseña' : 'Mostrar contraseña'"
      class="absolute right-2 top-1/2 -translate-y-1/2"
      @click="visible = !visible"
    >
      <Eye v-if="visible" class="h-5 w-5" />
      <EyeOff v-else class="h-5 w-5" />
    </IconButton>
  </div>
</template>

<script lang="ts" setup>
import { ref } from "vue";
import { Eye, EyeOff } from "@lucide/vue";
import IconButton from "@/components/shared/IconButton.vue";
import BaseInput from "@/components/shared/form/BaseInput.vue";
import type { FieldSize } from "@/types/shared/ui";

// Los attrs (id, placeholder, autocomplete…) van al input, no al wrapper.
defineOptions({ inheritAttrs: false });

withDefaults(defineProps<{ size?: FieldSize; invalid?: boolean }>(), {
  size: "md",
  invalid: false,
});

const model = defineModel<string>({ default: "" });

const visible = ref(false);
</script>
