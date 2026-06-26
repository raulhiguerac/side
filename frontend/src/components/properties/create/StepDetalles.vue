<template>
  <div>
    <h2 class="text-brand-text text-xl font-bold mb-1">Detalles de la propiedad</h2>
    <p class="text-brand-muted text-sm mb-6">Precio, características adicionales y descripción.</p>

    <!-- Precio + Admin fee -->
    <div class="mb-4">
      <label class="block text-xs font-semibold text-brand-muted uppercase tracking-wide mb-3">Precio</label>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs text-brand-muted mb-1.5">Precio de {{ form.listing_type === 'rent' ? 'arriendo' : 'venta' }}</label>
          <div class="relative">
            <DollarSign class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-muted" />
            <input
              :value="form.price"
              @input="emit('update:form', { ...form, price: +($event.target as HTMLInputElement).value || null })"
              type="number" min="1" step="1"
              placeholder="320.000.000"
              class="w-full border-2 border-brand-border rounded-xl pl-9 pr-3 py-2.5 text-sm text-brand-text focus:outline-none focus:border-brand-primary focus:ring-4 focus:ring-brand-primary/10 transition-all"
            />
          </div>
        </div>
        <div>
          <label class="block text-xs text-brand-muted mb-1.5">Administración <span class="text-brand-placeholder">(opcional)</span></label>
          <div class="relative">
            <DollarSign class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-muted" />
            <input
              :value="form.admin_fee"
              @input="emit('update:form', { ...form, admin_fee: +($event.target as HTMLInputElement).value || null })"
              type="number" min="0" step="1"
              placeholder="250.000"
              class="w-full border-2 border-brand-border rounded-xl pl-9 pr-3 py-2.5 text-sm text-brand-text focus:outline-none focus:border-brand-primary focus:ring-4 focus:ring-brand-primary/10 transition-all"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Parking + Piso/Pisos + Estrato + Año -->
    <div class="mb-4">
      <label class="block text-xs font-semibold text-brand-muted uppercase tracking-wide mb-3">Características</label>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs text-brand-muted mb-1.5">Parqueaderos</label>
          <div class="relative">
            <Car class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-muted" />
            <input
              :value="form.parking_spots"
              @input="emit('update:form', { ...form, parking_spots: +($event.target as HTMLInputElement).value })"
              type="number" min="0" step="1"
              placeholder="0"
              class="w-full border-2 border-brand-border rounded-xl pl-9 pr-3 py-2.5 text-sm text-brand-text focus:outline-none focus:border-brand-primary focus:ring-4 focus:ring-brand-primary/10 transition-all"
            />
          </div>
        </div>

        <!-- floor_number si apartment, total_floors si house -->
        <div v-if="form.property_type === 'apartment'">
          <label class="block text-xs text-brand-muted mb-1.5">Número de piso</label>
          <div class="relative">
            <Layers class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-muted" />
            <input
              :value="form.floor_number"
              @input="emit('update:form', { ...form, floor_number: +($event.target as HTMLInputElement).value || null })"
              type="number" min="0" step="1"
              placeholder="5"
              class="w-full border-2 border-brand-border rounded-xl pl-9 pr-3 py-2.5 text-sm text-brand-text focus:outline-none focus:border-brand-primary focus:ring-4 focus:ring-brand-primary/10 transition-all"
            />
          </div>
        </div>
        <div v-else-if="form.property_type === 'house'">
          <label class="block text-xs text-brand-muted mb-1.5">Total de pisos</label>
          <div class="relative">
            <Layers class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-muted" />
            <input
              :value="form.total_floors"
              @input="emit('update:form', { ...form, total_floors: +($event.target as HTMLInputElement).value || null })"
              type="number" min="1" step="1"
              placeholder="2"
              class="w-full border-2 border-brand-border rounded-xl pl-9 pr-3 py-2.5 text-sm text-brand-text focus:outline-none focus:border-brand-primary focus:ring-4 focus:ring-brand-primary/10 transition-all"
            />
          </div>
        </div>

        <div>
          <label class="block text-xs text-brand-muted mb-1.5">Estrato <span class="text-brand-placeholder">(opcional)</span></label>
          <div class="flex gap-1.5">
            <button
              v-for="s in [1,2,3,4,5,6]"
              :key="s"
              @click="emit('update:form', { ...form, stratum: form.stratum === s ? null : s })"
              :class="['flex-1 py-2.5 rounded-xl border-2 text-xs font-bold transition-all duration-200',
                form.stratum === s
                  ? 'border-brand-primary bg-brand-primary text-white'
                  : 'border-brand-border text-brand-muted hover:border-brand-primary/40']"
            >{{ s }}</button>
          </div>
        </div>

        <div>
          <label class="block text-xs text-brand-muted mb-1.5">Año de construcción <span class="text-brand-placeholder">(opcional)</span></label>
          <div class="relative">
            <Calendar class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-muted" />
            <input
              :value="form.year_built"
              @input="emit('update:form', { ...form, year_built: +($event.target as HTMLInputElement).value || null })"
              type="number" min="1800" :max="new Date().getFullYear()"
              placeholder="2010"
              class="w-full border-2 border-brand-border rounded-xl pl-9 pr-3 py-2.5 text-sm text-brand-text focus:outline-none focus:border-brand-primary focus:ring-4 focus:ring-brand-primary/10 transition-all"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Descripción -->
    <div>
      <label class="block text-xs font-semibold text-brand-muted uppercase tracking-wide mb-3">
        Descripción <span class="normal-case font-normal">(opcional)</span>
      </label>
      <textarea
        :value="form.description"
        @input="emit('update:form', { ...form, description: ($event.target as HTMLTextAreaElement).value })"
        rows="4"
        maxlength="2000"
        placeholder="Describe la propiedad: materiales, vista, acabados, puntos de interés cercanos..."
        class="w-full border-2 border-brand-border rounded-xl px-4 py-3 text-sm text-brand-text resize-none focus:outline-none focus:border-brand-primary focus:ring-4 focus:ring-brand-primary/10 transition-all"
      />
      <div class="text-right text-xs text-brand-muted mt-1">{{ form.description.length }} / 2000</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { DollarSign, Car, Layers, Calendar } from "@lucide/vue";
import type { CreatePropertyForm } from "@/types/properties";

defineProps<{ form: CreatePropertyForm }>();
const emit = defineEmits<{ (e: "update:form", v: CreatePropertyForm): void }>();
</script>
