<template>
  <div
    class="flex flex-col items-center justify-center flex-1 gap-6 text-center"
  >
    <span
      class="text-brand-muted text-xs font-semibold uppercase tracking-widest"
      >Valor estimado</span
    >
    <div class="flex flex-col gap-1">
      <p
        class="text-brand-text text-3xl sm:text-4xl lg:text-5xl font-bold leading-tight tracking-tight"
      >
        {{ formatCOP(tweened.value) }}
      </p>
      <p class="text-brand-muted text-sm">pesos colombianos</p>
    </div>
    <div class="flex flex-col gap-1.5 text-sm text-brand-muted">
      <span>± 11% error medio del modelo</span>
      <span>
        Barrio: <strong class="text-brand-text">{{ barrio }}</strong> · Estrato
        {{ estrato }}
      </span>
      <span class="text-xs text-brand-placeholder">bogota-avm · v1</span>
    </div>
    <button
      @click="emit('reset')"
      class="mt-2 text-sm text-brand-primary font-semibold hover:underline transition-colors"
    >
      ← Calcular de nuevo
    </button>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from "vue";
import gsap from "gsap";
import { formatCurrency } from "@/utils/money";

const props = defineProps<{
  price: number;
  barrio: string;
  estrato: number;
}>();
const emit = defineEmits<{ reset: [] }>();

const tweened = reactive({ value: 0 });

onMounted(() => {
  gsap.to(tweened, { duration: 1.5, value: props.price, ease: "power2.out" });
});

// `formatCurrency` ya redondea vía `maximumFractionDigits: 0`.
function formatCOP(value: number): string {
  return formatCurrency(value, "COP");
}
</script>

<style scoped></style>
