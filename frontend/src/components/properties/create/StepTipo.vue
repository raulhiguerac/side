<template>
  <div>
    <h2 class="text-brand-text text-xl font-bold mb-1">¿Qué vas a publicar?</h2>
    <p class="text-brand-muted text-sm mb-6">Selecciona el tipo de propiedad y las condiciones del negocio.</p>

    <!-- property_type + listing_type en grid 2x2 -->
    <div class="mb-4">
      <label class="block text-xs font-semibold text-brand-muted uppercase tracking-wide mb-3">Tipo de propiedad</label>
      <div class="grid grid-cols-2 gap-3">
        <button
          v-for="opt in propertyTypes"
          :key="opt.value"
          @click="emit('update:form', { ...form, property_type: opt.value })"
          :class="['group relative flex flex-col items-start gap-2 p-4 rounded-2xl border-2 text-left transition-all duration-200',
            form.property_type === opt.value
              ? 'border-brand-primary bg-brand-primary-light shadow-md shadow-green-100'
              : 'border-brand-border bg-white hover:-translate-y-0.5 hover:shadow-md hover:border-brand-primary/40']"
        >
          <component :is="opt.icon" class="w-6 h-6" :class="form.property_type === opt.value ? 'text-brand-primary' : 'text-brand-muted'" />
          <div>
            <div class="text-sm font-semibold text-brand-text">{{ opt.label }}</div>
            <div class="text-xs text-brand-muted">{{ opt.desc }}</div>
          </div>
          <div v-if="form.property_type === opt.value" class="absolute top-3 right-3">
            <div class="w-5 h-5 rounded-full bg-brand-primary flex items-center justify-center">
              <Check class="w-3 h-3 text-white" />
            </div>
          </div>
        </button>
      </div>
    </div>

    <div class="mb-4">
      <label class="block text-xs font-semibold text-brand-muted uppercase tracking-wide mb-3">Tipo de negocio</label>
      <div class="grid grid-cols-2 gap-3">
        <button
          v-for="opt in listingTypes"
          :key="opt.value"
          @click="emit('update:form', { ...form, listing_type: opt.value })"
          :class="['group relative flex flex-col items-start gap-2 p-4 rounded-2xl border-2 text-left transition-all duration-200',
            form.listing_type === opt.value
              ? 'border-brand-primary bg-brand-primary-light shadow-md shadow-green-100'
              : 'border-brand-border bg-white hover:-translate-y-0.5 hover:shadow-md hover:border-brand-primary/40']"
        >
          <component :is="opt.icon" class="w-6 h-6" :class="form.listing_type === opt.value ? 'text-brand-primary' : 'text-brand-muted'" />
          <div>
            <div class="text-sm font-semibold text-brand-text">{{ opt.label }}</div>
            <div class="text-xs text-brand-muted">{{ opt.desc }}</div>
          </div>
          <div v-if="form.listing_type === opt.value" class="absolute top-3 right-3">
            <div class="w-5 h-5 rounded-full bg-brand-primary flex items-center justify-center">
              <Check class="w-3 h-3 text-white" />
            </div>
          </div>
        </button>
      </div>
    </div>

    <!-- condition + currency en fila -->
    <div class="grid grid-cols-2 gap-4 mb-4">
      <div>
        <label class="block text-xs font-semibold text-brand-muted uppercase tracking-wide mb-3">Condición</label>
        <div class="flex gap-2">
          <button
            v-for="opt in conditions"
            :key="opt.value"
            @click="emit('update:form', { ...form, condition: opt.value })"
            :class="['flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl border-2 text-sm font-medium transition-all duration-200',
              form.condition === opt.value
                ? 'border-brand-primary bg-brand-primary-light text-brand-primary'
                : 'border-brand-border text-brand-text hover:border-brand-primary/40']"
          >
            <component :is="opt.icon" class="w-4 h-4" />
            {{ opt.label }}
          </button>
        </div>
      </div>

      <div>
        <label class="block text-xs font-semibold text-brand-muted uppercase tracking-wide mb-3">Moneda</label>
        <div class="grid grid-cols-6 gap-1.5">
          <button
            v-for="c in currencies"
            :key="c"
            @click="emit('update:form', { ...form, currency: c })"
            :class="['flex items-center justify-center py-2.5 rounded-xl border-2 text-xs font-semibold transition-all duration-200',
              form.currency === c
                ? 'border-brand-primary bg-brand-primary text-white shadow-sm'
                : 'border-brand-border text-brand-muted hover:border-brand-primary/40 hover:text-brand-primary']"
          >{{ c }}</button>
        </div>
      </div>
    </div>

    <!-- area + bedrooms + bathrooms -->
    <div class="grid grid-cols-3 gap-3">
      <div v-for="field in numericFields" :key="field.key">
        <label class="block text-xs font-semibold text-brand-muted uppercase tracking-wide mb-2">{{ field.label }}</label>
        <div class="relative">
          <component :is="field.icon" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-muted" />
          <input
            :value="(form as any)[field.key]"
            @input="emit('update:form', { ...form, [field.key]: +($event.target as HTMLInputElement).value || null })"
            :type="'number'"
            :min="field.min"
            :step="field.step"
            :placeholder="field.placeholder"
            class="w-full border-2 border-brand-border rounded-xl pl-9 pr-3 py-2.5 text-sm text-brand-text focus:outline-none focus:border-brand-primary focus:ring-4 focus:ring-brand-primary/10 transition-all"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Home, Building2, Tag, Key, Sparkles, Clock, Maximize2, BedDouble, Bath, Check } from "@lucide/vue";
import type { CreatePropertyForm } from "@/types/properties";

defineProps<{ form: CreatePropertyForm }>();
const emit = defineEmits<{ (e: "update:form", v: CreatePropertyForm): void }>();

const propertyTypes = [
  { value: "house",     label: "Casa",        desc: "Ideal para familias",     icon: Home      },
  { value: "apartment", label: "Apartamento", desc: "Vida urbana y moderna",   icon: Building2 },
];
const listingTypes = [
  { value: "sale", label: "Venta",    desc: "Transfiere la propiedad", icon: Tag },
  { value: "rent", label: "Arriendo", desc: "Ingreso mensual fijo",    icon: Key },
];
const conditions = [
  { value: "new",  label: "Nueva",  icon: Sparkles },
  { value: "used", label: "Usada",  icon: Clock    },
];
const currencies = ["COP", "USD", "EUR", "MXN", "PEN", "CLP"];

const numericFields = [
  { key: "area_m2",   label: "Área (m²)",      icon: Maximize2, min: "1",   step: "0.01", placeholder: "85.00" },
  { key: "bedrooms",  label: "Habitaciones",   icon: BedDouble, min: "1",   step: "1",    placeholder: "3"     },
  { key: "bathrooms", label: "Baños",          icon: Bath,      min: "1",   step: "0.5",  placeholder: "2"     },
];
</script>
