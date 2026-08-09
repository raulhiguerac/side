<template>
  <BaseModal :model-value="modelValue" @update:model-value="close">
    <h2 class="text-brand-text text-lg font-semibold mb-1">
      Importar propiedades (CSV)
    </h2>
    <p class="text-brand-muted text-sm mb-4">
      El archivo se procesa en segundo plano. Podés seguir trabajando y revisar
      el resultado más tarde.
    </p>

    <input
      type="file"
      accept=".csv"
      :disabled="uploading"
      @change="onFileChange"
      class="block w-full text-sm text-brand-muted mb-4"
    />

    <p v-if="error" class="text-red-500 text-sm mb-4">{{ error }}</p>

    <div class="flex justify-end gap-3">
      <button
        :disabled="uploading"
        @click="close"
        class="px-4 py-2 rounded-xl text-sm font-medium text-brand-muted hover:bg-brand-bg transition-colors disabled:opacity-50"
      >
        Cancelar
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
const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  queued: [batchId: string];
}>();

interface BulkUploadUrl {
  storage_key: string;
  upload_url: string;
  max_size_bytes: number;
  expires_in: number;
}

interface BulkJobAccepted {
  batch_id: string;
}

const file = ref<File | null>(null);
const uploading = ref(false);
const error = ref("");

function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement;
  file.value = target.files?.[0] ?? null;
  error.value = "";
}

/** Presigned PUT → upload directo a storage → key de vuelta a la API. Al submit: la URL expira en 5 min. */
async function upload() {
  if (!file.value || uploading.value) return;

  uploading.value = true;
  error.value = "";

  try {
    const { data: presigned } = await propertiesApi.post<BulkUploadUrl>(
      "/v1/admin/properties/bulk/upload-url",
      { filename: file.value.name }
    );

    if (file.value.size > presigned.max_size_bytes) {
      // A plain presigned PUT can't enforce a size limit, so this check is the only one there is.
      const maxMb = Math.round(presigned.max_size_bytes / 1024 / 1024);
      error.value = `El archivo supera el máximo de ${maxMb} MB.`;
      return;
    }

    // Straight to storage: extra credentials can make the signed request fail.
    const stored = await fetch(presigned.upload_url, {
      method: "PUT",
      body: file.value,
    });
    if (!stored.ok) {
      throw new Error(`storage responded ${stored.status}`);
    }

    const { data: job } = await propertiesApi.post<BulkJobAccepted>(
      "/v1/admin/properties/bulk",
      { storage_key: presigned.storage_key }
    );

    emit("queued", job.batch_id);
    close();
  } catch (e) {
    error.value =
      "No se pudo iniciar la importación. Verificá el archivo e intentá de nuevo.";
    console.error("bulk import failed", e);
  } finally {
    uploading.value = false;
  }
}

function close() {
  file.value = null;
  error.value = "";
  emit("update:modelValue", false);
}
</script>
