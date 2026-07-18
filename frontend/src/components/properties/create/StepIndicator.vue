<template>
  <div class="px-8 py-6 border-b border-brand-divider">
    <div class="flex items-center">
      <template v-for="(step, i) in steps" :key="i">
        <!-- Circle -->
        <div class="flex flex-col items-center gap-1.5">
          <div
            class="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300"
            :class="
              i < current
                ? 'bg-brand-primary text-white shadow-md shadow-green-200'
                : i === current
                ? 'bg-brand-primary text-white shadow-lg shadow-green-300 scale-110'
                : 'bg-brand-divider text-brand-muted'
            "
          >
            <Check v-if="i < current" class="w-4 h-4" />
            <span v-else>{{ i + 1 }}</span>
          </div>
          <span
            class="text-xs font-medium whitespace-nowrap"
            :class="i <= current ? 'text-brand-primary' : 'text-brand-muted'"
            >{{ step }}</span
          >
        </div>

        <!-- Bar -->
        <div
          v-if="i < steps.length - 1"
          class="flex-1 h-0.5 mx-2 mb-4 rounded-full overflow-hidden bg-brand-divider"
        >
          <div
            class="h-full bg-brand-primary transition-all duration-500"
            :style="{ width: i < current ? '100%' : '0%' }"
          />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Check } from "@lucide/vue";
defineProps<{ steps: string[]; current: number }>();
</script>
