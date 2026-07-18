<template>
  <BaseModal :model-value="modelValue" @update:model-value="close">
    <h2 class="text-brand-text text-lg font-semibold mb-1">
      Importar propiedades (CSV)
    </h2>
    <p class="text-brand-muted text-sm mb-4">
      Sube un archivo CSV con las propiedades a crear en bloque.
    </p>

    <input
      type="file"
      accept=".csv,.json"
      @change="onFileChange"
      class="block w-full text-sm text-brand-muted mb-4"
    />

    <div v-if="result" class="mb-4 text-sm">
      <p class="text-brand-primary font-medium">
        {{ result.inserted }} propiedades creadas.
      </p>
      <ul v-if="result.errors.length" class="mt-2 text-red-500 list-disc pl-5">
        <li v-for="(err, i) in result.errors" :key="i">{{ err }}</li>
      </ul>
    </div>

    <p v-if="error" class="text-red-500 text-sm mb-4">{{ error }}</p>

    <div class="flex justify-end gap-3">
      <button
        @click="close"
        class="px-4 py-2 rounded-xl text-sm font-medium text-brand-muted hover:bg-brand-bg transition-colors"
      >
        Cerrar
      </button>
      <button
        :disabled="!file || uploading"
        @click="upload"
        class="px-4 py-2 rounded-xl bg-brand-primary text-white text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
      >
        {{ uploading ? "Subiendo..." : "Subir" }}
      </button>
    </div>
  </BaseModal>
</template>

<script lang="ts" setup>
import { ref } from "vue";
import BaseModal from "@/components/shared/BaseModal.vue";
import propertiesApi from "@/api/propertiesApi";

defineProps<{ modelValue: boolean }>();
const emit = defineEmits(["update:modelValue"]);

interface BulkCreatePropertiesResult {
  inserted: number;
  errors: string[];
}

const file = ref<File | null>(null);
const uploading = ref(false);
const result = ref<BulkCreatePropertiesResult | null>(null);
const error = ref("");

function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement;
  file.value = target.files?.[0] ?? null;
  result.value = null;
  error.value = "";
}

async function upload() {
  if (!file.value) return;
  uploading.value = true;
  error.value = "";
  try {
    const formData = new FormData();
    formData.append("file", file.value);
    const { data } = await propertiesApi.post<BulkCreatePropertiesResult>(
      "/v1/admin/properties/bulk",
      formData
    );
    result.value = data;
  } catch (e) {
    error.value = "Error al subir el archivo. Verificá el formato e intentá de nuevo.";
  } finally {
    uploading.value = false;
  }
}

function close() {
  file.value = null;
  result.value = null;
  error.value = "";
  emit("update:modelValue", false);
}
</script>
