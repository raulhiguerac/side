<template>
  <div class="py-2">
    <!-- Drop zone -->
    <div
      @click="inputRef?.click()"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="onDrop"
      :class="[
        'border-2 border-dashed rounded-2xl flex flex-col items-center justify-center cursor-pointer transition-colors select-none',
        files.length ? 'py-6' : 'py-16',
        isDragging
          ? 'border-brand-primary bg-brand-primary-light'
          : 'border-brand-border hover:border-brand-primary hover:bg-green-50',
      ]"
    >
      <div class="flex flex-col items-center gap-2 pointer-events-none">
        <div
          class="w-12 h-12 rounded-full bg-brand-bg flex items-center justify-center"
        >
          <Camera class="w-6 h-6 text-brand-muted" />
        </div>
        <p class="text-sm font-semibold text-brand-text">
          {{ files.length ? "Agregar más fotos" : "Arrastra tus fotos aquí" }}
        </p>
        <p class="text-xs text-brand-muted">o haz click para seleccionar</p>
        <p v-if="!files.length" class="text-xs text-brand-muted mt-0.5">
          JPG, PNG o WEBP · máx. {{ max }} fotos
        </p>
      </div>
    </div>

    <!-- Counter -->
    <p v-if="files.length" class="text-sm text-brand-muted mt-3">
      <span class="font-semibold text-brand-text">{{ files.length }}</span>
      / {{ max }} fotos seleccionadas
    </p>

    <!-- Preview grid -->
    <div
      v-if="files.length"
      class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 mt-3"
    >
      <div
        v-for="(preview, i) in previews"
        :key="i"
        class="relative aspect-square"
      >
        <img
          :src="preview"
          :alt="`Foto ${i + 1}`"
          class="w-full h-full object-cover rounded-xl border border-brand-divider"
        />

        <button
          @click.stop="removeFile(i)"
          class="absolute top-1.5 right-1.5 w-6 h-6 rounded-full bg-white shadow border border-brand-border flex items-center justify-center hover:bg-red-50 transition-colors"
        >
          <X class="w-3.5 h-3.5 text-brand-muted" />
        </button>

        <span
          v-if="i === 0 && !hasExistingPhotos"
          class="absolute bottom-1.5 left-1.5 text-[10px] font-semibold bg-brand-primary text-white px-1.5 py-0.5 rounded-md"
        >
          Portada
        </span>
      </div>
    </div>

    <!-- Hidden file input -->
    <input
      ref="inputRef"
      type="file"
      multiple
      accept="image/*"
      class="hidden"
      @change="onSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from "vue";
import { Camera, X } from "@lucide/vue";

const props = defineProps<{
  max: number;
  hasExistingPhotos: boolean;
}>();

const files = defineModel<File[]>({ default: () => [] });

const inputRef = ref<HTMLInputElement | null>(null);
const isDragging = ref(false);
/** Efecto y no `computed`: leer y escribir el mismo ref se auto-invalidaba y revocaba URLs en uso. */
const previews = ref<string[]>([]);

watch(
  files,
  (list) => {
    previews.value.forEach(URL.revokeObjectURL);
    previews.value = list.map((f) => URL.createObjectURL(f));
  },
  { immediate: true }
);

function addFiles(list: FileList | null) {
  if (!list) return;
  const slots = props.max - files.value.length;
  if (slots <= 0) return;
  const incoming = Array.from(list)
    .filter((f) => f.type.startsWith("image/"))
    .slice(0, slots);
  files.value = [...files.value, ...incoming];
}

function onSelect(e: Event) {
  addFiles((e.target as HTMLInputElement).files);
  if (inputRef.value) inputRef.value.value = "";
}

function onDrop(e: DragEvent) {
  isDragging.value = false;
  addFiles(e.dataTransfer?.files ?? null);
}

function removeFile(i: number) {
  const next = [...files.value];
  next.splice(i, 1);
  files.value = next;
}

onUnmounted(() => previews.value.forEach(URL.revokeObjectURL));
</script>
