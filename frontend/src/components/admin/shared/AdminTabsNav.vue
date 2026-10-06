<template>
  <nav class="flex border-b border-brand-divider">
    <RouterLink
      v-for="tab in tabs"
      :key="tab.to"
      :to="tab.to"
      custom
      v-slot="{ href, navigate, isActive, isExactActive }"
    >
      <!-- `custom` + `<a>`: con `active-class` gana la clase que Tailwind emitió última. -->
      <a
        :href="href"
        @click="navigate"
        class="-mb-px border-b-2 pb-3 text-center text-sm font-medium transition-colors"
        :class="[
          stretch ? 'flex-1' : 'px-5',
          (isPrefixOfAnother(tab.to) ? isExactActive : isActive)
            ? 'border-brand-primary text-brand-primary'
            : 'border-transparent text-brand-muted hover:text-brand-text',
        ]"
      >
        {{ tab.label }}
      </a>
    </RouterLink>
  </nav>
</template>

<script lang="ts" setup>
import { RouterLink } from "vue-router";

const props = withDefaults(
  defineProps<{
    tabs: readonly { label: string; to: string }[];
    /** Reparte el ancho entre las tabs; sin esto cada una ocupa lo que mide. */
    stretch?: boolean;
  }>(),
  { stretch: false }
);

// Una ruta prefijo de otra matchea exacto; si no, queda activa en la de abajo.
function isPrefixOfAnother(to: string): boolean {
  return props.tabs.some((tab) => tab.to !== to && tab.to.startsWith(`${to}/`));
}
</script>
