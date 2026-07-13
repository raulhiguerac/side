<template>
  <div class="bg-white rounded-2xl border border-brand-divider p-6 flex-1">
    <label
      class="block text-xs font-semibold text-brand-muted uppercase tracking-wide mb-3"
    >
      Detalles
    </label>

    <div class="grid grid-cols-2 gap-3 mb-4">
      <div>
        <label class="block text-xs text-brand-muted mb-1.5">Precio</label>
        <div class="relative">
          <DollarSign
            class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-muted"
          />
          <input
            :value="displayPrice"
            @focus="displayPrice = form.price ? String(form.price) : ''"
            @blur="displayPrice = formatMoney(form.price)"
            @input="onPriceInput"
            type="text"
            inputmode="numeric"
            class="w-full border-2 border-brand-border rounded-xl pl-9 pr-3 py-2.5 text-sm text-brand-text focus:outline-none focus:border-brand-primary focus:ring-4 focus:ring-brand-primary/10 transition-all"
          />
        </div>
      </div>
      <div>
        <label class="block text-xs text-brand-muted mb-1.5"
          >Administración
          <span class="text-brand-placeholder">(opcional)</span></label
        >
        <div class="relative">
          <DollarSign
            class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-muted"
          />
          <input
            :value="displayAdminFee"
            @focus="
              displayAdminFee = form.admin_fee ? String(form.admin_fee) : ''
            "
            @blur="displayAdminFee = formatMoney(form.admin_fee)"
            @input="onAdminFeeInput"
            type="text"
            inputmode="numeric"
            class="w-full border-2 border-brand-border rounded-xl pl-9 pr-3 py-2.5 text-sm text-brand-text focus:outline-none focus:border-brand-primary focus:ring-4 focus:ring-brand-primary/10 transition-all"
          />
        </div>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4 mb-4">
      <div>
        <label
          class="block text-xs font-semibold text-brand-muted uppercase tracking-wide mb-3"
          >Condición</label
        >
        <div class="flex gap-2">
          <button
            v-for="opt in conditions"
            :key="opt.value"
            type="button"
            @click="emit('update:form', { ...form, condition: opt.value })"
            :class="[
              'flex-1 py-2.5 rounded-xl border-2 text-sm font-medium transition-all duration-200',
              form.condition === opt.value
                ? 'border-brand-primary bg-brand-primary-light text-brand-primary'
                : 'border-brand-border text-brand-text hover:border-brand-primary/40',
            ]"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>

      <div>
        <label
          class="block text-xs font-semibold text-brand-muted uppercase tracking-wide mb-3"
          >Moneda</label
        >
        <div class="flex flex-wrap justify-center gap-2">
          <button
            v-for="c in currencies"
            :key="c"
            type="button"
            @click="emit('update:form', { ...form, currency: c })"
            :class="[
              'flex items-center justify-center px-3 py-3 rounded-xl border-2 text-xs font-semibold transition-all duration-200 w-[calc(25%-0.375rem)]',
              form.currency === c
                ? 'border-brand-primary bg-brand-primary text-white shadow-sm'
                : 'border-brand-border text-brand-muted hover:border-brand-primary/40 hover:text-brand-primary',
            ]"
          >
            {{ c }}
          </button>
        </div>
      </div>
    </div>

    <div>
      <label
        class="block text-xs font-semibold text-brand-muted uppercase tracking-wide mb-3"
      >
        Descripción
        <span class="normal-case font-normal">(opcional)</span>
      </label>
      <textarea
        :value="form.description"
        @input="
          emit('update:form', {
            ...form,
            description: ($event.target as HTMLTextAreaElement).value,
          })
        "
        rows="3"
        maxlength="2000"
        class="w-full border-2 border-brand-border rounded-xl px-4 py-3 text-sm text-brand-text resize-none focus:outline-none focus:border-brand-primary focus:ring-4 focus:ring-brand-primary/10 transition-all"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch } from "vue";
import { DollarSign } from "@lucide/vue";
import { formatMoney, parseMoney } from "@/utils/money";
import type { PropertyEditForm as EditForm } from "@/types/properties";

const props = defineProps<{ form: EditForm }>();
const emit = defineEmits<{ (e: "update:form", v: EditForm): void }>();

const conditions: { value: EditForm["condition"]; label: string }[] = [
  { value: "new", label: "Nueva" },
  { value: "used", label: "Usada" },
  { value: "remodeled", label: "Remodelada" },
];

const currencies: EditForm["currency"][] = [
  "COP",
  "USD",
  "EUR",
  "MXN",
  "PEN",
  "CLP",
  "ARS",
];

const displayPrice = ref(formatMoney(props.form.price));
const displayAdminFee = ref(formatMoney(props.form.admin_fee));

watch(
  () => props.form.price,
  (v) => {
    displayPrice.value = formatMoney(v);
  }
);
watch(
  () => props.form.admin_fee,
  (v) => {
    displayAdminFee.value = formatMoney(v);
  }
);

function onPriceInput(event: Event) {
  const price = parseMoney((event.target as HTMLInputElement).value) ?? 0;
  emit("update:form", { ...props.form, price });
}

function onAdminFeeInput(event: Event) {
  const admin_fee = parseMoney((event.target as HTMLInputElement).value);
  emit("update:form", { ...props.form, admin_fee });
}
</script>
