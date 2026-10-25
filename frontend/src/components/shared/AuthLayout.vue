<template>
  <div
    class="min-h-screen bg-brand-bg flex items-center justify-center p-4 sm:p-8 lg:p-12"
  >
    <div
      class="flex flex-col lg:flex-row w-full max-w-5xl bg-white rounded-2xl lg:rounded-3xl shadow-[0_20px_60px_-12px_rgba(0,0,0,0.08)] overflow-hidden"
    >
      <div
        class="w-full lg:w-1/2 bg-brand-dark flex flex-col items-center justify-center gap-6 p-8 sm:p-12 lg:p-16"
      >
        <div class="flex-1 flex items-center justify-center w-full">
          <img
            :src="illustration"
            alt=""
            class="w-3/4 max-w-sm lg:max-w-md h-auto"
          />
        </div>
        <div class="text-left space-y-3">
          <h2
            class="text-center text-white text-base sm:text-lg lg:text-xl font-bold"
          >
            {{ title }}
          </h2>
          <p class="text-white/80 text-xs sm:text-sm">{{ subtitle }}</p>
          <slot name="aside" />
        </div>
      </div>
      <div
        class="w-full lg:w-1/2 bg-white p-6 sm:p-10 lg:p-16 flex flex-col items-center justify-center"
      >
        <slot />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
// `aside` va debajo del subtítulo, para extras como los bullets del login.
defineProps<{ illustration: string; title: string; subtitle: string }>();
</script>
