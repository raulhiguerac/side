<template>
  <div>
    <h2 class="text-brand-text text-xl font-bold mb-1">¿Qué vas a publicar?</h2>
    <p class="text-brand-muted text-sm mb-6">
      Selecciona el tipo de propiedad y las condiciones del negocio.
    </p>

    <!-- property_type + listing_type en grid 2x2 -->
    <div class="mb-4">
      <label
        class="block text-xs font-semibold mb-3"
        :class="
          attempted && !form.property_type
            ? 'text-brand-danger'
            : 'text-brand-muted uppercase tracking-wide'
        "
        >Tipo de propiedad<span
          v-if="attempted && !form.property_type"
          class="ml-1 normal-case"
          >— requerido</span
        ></label
      >
      <div
        class="grid grid-cols-2 gap-3"
        :class="
          attempted && !form.property_type
            ? 'ring-2 ring-brand-danger-border rounded-2xl p-1'
            : ''
        "
      >
        <OptionCard
          v-for="opt in propertyTypes"
          :key="opt.value"
          :selected="form.property_type === opt.value"
          @click="emit('update:form', { ...form, property_type: opt.value })"
          class="group relative flex flex-col items-start gap-2 p-4"
        >
          <component
            :is="opt.icon"
            class="w-6 h-6"
            :class="
              form.property_type === opt.value
                ? 'text-brand-primary'
                : 'text-brand-muted'
            "
          />
          <div>
            <div class="text-sm font-semibold text-brand-text">
              {{ opt.label }}
            </div>
            <div class="text-xs text-brand-muted">{{ opt.desc }}</div>
          </div>
          <div
            v-if="form.property_type === opt.value"
            class="absolute top-3 right-3"
          >
            <div
              class="w-5 h-5 rounded-full bg-brand-primary flex items-center justify-center"
            >
              <Check class="w-3 h-3 text-white" />
            </div>
          </div>
        </OptionCard>
      </div>
    </div>

    <div class="mb-4">
      <label
        class="block text-xs font-semibold mb-3"
        :class="
          attempted && !form.listing_type
            ? 'text-brand-danger'
            : 'text-brand-muted uppercase tracking-wide'
        "
        >Tipo de negocio<span
          v-if="attempted && !form.listing_type"
          class="ml-1 normal-case"
          >— requerido</span
        ></label
      >
      <div
        class="grid grid-cols-2 gap-3"
        :class="
          attempted && !form.listing_type
            ? 'ring-2 ring-brand-danger-border rounded-2xl p-1'
            : ''
        "
      >
        <OptionCard
          v-for="opt in listingTypes"
          :key="opt.value"
          :selected="form.listing_type === opt.value"
          @click="emit('update:form', { ...form, listing_type: opt.value })"
          class="group relative flex flex-col items-start gap-2 p-4"
        >
          <component
            :is="opt.icon"
            class="w-6 h-6"
            :class="
              form.listing_type === opt.value
                ? 'text-brand-primary'
                : 'text-brand-muted'
            "
          />
          <div>
            <div class="text-sm font-semibold text-brand-text">
              {{ opt.label }}
            </div>
            <div class="text-xs text-brand-muted">{{ opt.desc }}</div>
          </div>
          <div
            v-if="form.listing_type === opt.value"
            class="absolute top-3 right-3"
          >
            <div
              class="w-5 h-5 rounded-full bg-brand-primary flex items-center justify-center"
            >
              <Check class="w-3 h-3 text-white" />
            </div>
          </div>
        </OptionCard>
      </div>
    </div>

    <!-- condition + currency en fila -->
    <div class="grid grid-cols-2 gap-4 mb-4">
      <div>
        <label
          class="block text-xs font-semibold mb-3"
          :class="
            attempted && !form.condition
              ? 'text-brand-danger'
              : 'text-brand-muted uppercase tracking-wide'
          "
          >Condición<span
            v-if="attempted && !form.condition"
            class="ml-1 normal-case"
            >— requerido</span
          ></label
        >
        <div
          class="flex gap-2"
          :class="
            attempted && !form.condition
              ? 'ring-2 ring-brand-danger-border rounded-xl p-1'
              : ''
          "
        >
          <ChoiceChip
            v-for="opt in conditions"
            :key="opt.value"
            :selected="form.condition === opt.value"
            @click="emit('update:form', { ...form, condition: opt.value })"
            class="flex-1"
          >
            <component :is="opt.icon" class="w-4 h-4" />
            {{ opt.label }}
          </ChoiceChip>
        </div>
      </div>

      <div>
        <label
          class="block text-xs font-semibold text-brand-muted uppercase tracking-wide mb-3"
          >Moneda</label
        >
        <div class="grid grid-cols-6 gap-1.5">
          <ChoiceChip
            v-for="c in currencies"
            :key="c"
            :selected="form.currency === c"
            @click="emit('update:form', { ...form, currency: c })"
          >
            {{ c }}
          </ChoiceChip>
        </div>
      </div>
    </div>

    <!-- area + bedrooms + bathrooms -->
    <div class="grid grid-cols-3 gap-3">
      <div v-for="field in numericFields" :key="field.key">
        <label
          class="block text-xs font-semibold text-brand-muted uppercase tracking-wide mb-2"
          >{{ field.label }}</label
        >
        <div class="relative">
          <component
            :is="field.icon"
            class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-muted"
          />
          <BaseInput
            :invalid="attempted && !form[field.key]"
            :value="form[field.key]"
            @input="
              emit('update:form', {
                ...form,
                [field.key]: +($event.target as HTMLInputElement).value || null,
              })
            "
            :type="'number'"
            :min="field.min"
            :step="field.step"
            :placeholder="field.placeholder"
            class="pl-9"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import BaseInput from "@/components/shared/form/BaseInput.vue";
import ChoiceChip from "@/components/shared/ChoiceChip.vue";
import OptionCard from "@/components/shared/OptionCard.vue";
import {
  Home,
  Building2,
  Tag,
  Key,
  Sparkles,
  Clock,
  Maximize2,
  BedDouble,
  Bath,
  Check,
} from "@lucide/vue";
import {
  LISTING_TYPE_LABELS,
  PROPERTY_TYPE_LABELS,
} from "@/constants/propertyLabels";
import type { ListingType, PropertyType } from "@/types/properties/base";
import type { ChoiceOption } from "@/types/shared/ui";
import type {
  CreateStepEmits,
  CreateStepProps,
  NumericFieldOption,
} from "@/types/properties/forms";

defineProps<CreateStepProps>();
const emit = defineEmits<CreateStepEmits>();

const propertyTypes: ChoiceOption<PropertyType>[] = [
  {
    value: "house",
    label: PROPERTY_TYPE_LABELS.house,
    desc: "Ideal para familias",
    icon: Home,
  },
  {
    value: "apartment",
    label: PROPERTY_TYPE_LABELS.apartment,
    desc: "Vida urbana y moderna",
    icon: Building2,
  },
];
const listingTypes: ChoiceOption<ListingType>[] = [
  {
    value: "sale",
    label: LISTING_TYPE_LABELS.sale,
    desc: "Transfiere la propiedad",
    icon: Tag,
  },
  {
    value: "rent",
    label: LISTING_TYPE_LABELS.rent,
    desc: "Ingreso mensual fijo",
    icon: Key,
  },
];
const conditions = [
  { value: "new", label: "Nueva", icon: Sparkles },
  { value: "used", label: "Usada", icon: Clock },
];
const currencies = ["COP", "USD", "EUR", "MXN", "PEN", "CLP"];

const numericFields: NumericFieldOption[] = [
  {
    key: "area_m2",
    label: "Área (m²)",
    icon: Maximize2,
    min: "1",
    step: "0.01",
    placeholder: "85.00",
  },
  {
    key: "bedrooms",
    label: "Habitaciones",
    icon: BedDouble,
    min: "1",
    step: "1",
    placeholder: "3",
  },
  {
    key: "bathrooms",
    label: "Baños",
    icon: Bath,
    min: "1",
    step: "0.5",
    placeholder: "2",
  },
];
</script>
