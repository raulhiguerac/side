<template>
  <!-- Header: title + badges -->
  <div class="flex items-start justify-between gap-4">
    <div>
      <h1 class="text-2xl font-semibold text-brand-text">{{ title }}</h1>
      <p class="text-sm text-brand-muted mt-0.5">{{ locationLabel }}</p>
    </div>
    <div class="flex items-center gap-2 shrink-0">
      <span
        :class="statusStyle"
        class="px-[10px] py-0.5 rounded-full text-xs font-medium"
      >
        {{ statusLabel }}
      </span>
      <div class="relative group">
        <span
          :class="verificationStyle"
          class="px-[10px] py-0.5 rounded-full text-xs font-medium cursor-default"
        >
          {{ verificationLabel }}
        </span>
        <div
          class="hidden group-hover:block absolute top-[calc(100%+6px)] right-0 w-56 bg-gray-800 text-gray-100 text-[0.7rem] leading-snug p-2 rounded-lg z-10"
        >
          Certificamos que el anuncio cumple nuestras reglas de moderación y que
          la propiedad pertenece al publicante.
        </div>
      </div>
    </div>
  </div>

  <!-- Price -->
  <div class="space-y-1">
    <p class="text-3xl font-bold text-brand-text">{{ formattedPrice }}</p>
    <p v-if="hasAdminFee" class="text-sm text-brand-muted">
      Admin: {{ formattedAdminFee }}
    </p>
  </div>

  <!-- Stats chips -->
  <div class="grid grid-cols-3 sm:grid-cols-6 gap-3">
    <div
      v-for="stat in stats"
      :key="stat.label"
      class="flex flex-col items-center gap-0.5 px-4 py-2 border border-brand-divider rounded-xl"
    >
      <span class="text-brand-muted text-xs">{{ stat.label }}</span>
      <span class="font-medium text-brand-text text-sm">{{ stat.value }}</span>
    </div>
  </div>

  <!-- Description -->
  <div v-if="description" class="space-y-2">
    <h2 class="text-base font-semibold text-brand-text">Descripción</h2>
    <p class="text-brand-muted text-sm leading-relaxed">
      {{ description }}
    </p>
  </div>

  <!-- Secondary details -->
  <div class="space-y-2">
    <h2 class="text-base font-semibold text-brand-text">Detalles</h2>
    <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
      <div
        v-for="detail in details"
        :key="detail.label"
        class="flex flex-col gap-0.5 px-3 py-2 bg-gray-50 rounded-[10px]"
      >
        <span class="text-brand-muted text-xs">{{ detail.label }}</span>
        <span class="text-brand-text text-sm font-medium">{{
          detail.value
        }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  locationLabel: string;
  statusLabel: string;
  statusStyle: string;
  verificationLabel: string;
  verificationStyle: string;
  formattedPrice: string;
  formattedAdminFee: string;
  hasAdminFee: boolean;
  description: string | null;
  stats: Array<{ label: string; value: string | number }>;
  details: Array<{ label: string; value: string | number }>;
}>();
</script>
