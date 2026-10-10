<template>
  <div class="space-y-4">
    <dl class="grid grid-cols-2 gap-3">
      <div
        v-for="stat in stats"
        :key="stat.label"
        class="bg-brand-bg rounded-xl px-4 py-3"
      >
        <dt class="text-brand-muted text-xs">{{ stat.label }}</dt>
        <dd class="text-brand-text text-2xl font-bold tabular-nums">
          {{ stat.value }}
        </dd>
      </div>
    </dl>

    <div v-if="issues.length">
      <p class="text-brand-text mb-2 text-sm font-medium">
        {{ issuesTitle }} ({{ issues.length }})
      </p>
      <ul
        class="border-brand-divider text-brand-muted max-h-40 space-y-1 overflow-y-auto rounded-xl border px-4 py-3 text-sm"
      >
        <li v-for="issue in issues" :key="issue">{{ issue }}</li>
      </ul>
    </div>
  </div>
</template>

<script lang="ts" setup>
defineProps<{
  stats: readonly { label: string; value: number }[];
  issuesTitle: string;
  issues: readonly string[];
}>();
</script>
