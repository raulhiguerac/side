<template>
  <div class="bg-brand-bg px-[5%] sm:px-[8%] lg:px-[10%] pt-6 pb-12">
    <!-- Hero card -->
    <div
      class="w-full min-h-[70vh] rounded-3xl overflow-hidden shadow-2xl bg-brand-dark flex flex-col md:flex-row"
    >
      <!-- Left: copy -->
      <div
        class="flex-1 flex flex-col justify-center gap-8 lg:gap-12 px-8 py-8 lg:px-14 lg:py-12"
      >
        <div class="flex flex-col gap-3">
          <h1 class="text-white text-3xl lg:text-5xl font-bold leading-tight">
            El inmueble que buscas,<br />sin pagar de más.
          </h1>
          <p
            class="text-white/60 text-sm lg:text-base max-w-sm leading-relaxed"
          >
            Más de
            <strong class="text-white font-semibold">53.000 propiedades</strong>
            analizadas. Descubre el valor real de cualquier inmueble en
            segundos.
          </p>
        </div>
        <div class="flex flex-col sm:flex-row gap-3">
          <router-link
            to="/login"
            class="w-full sm:w-56 text-center bg-brand-primary text-white text-sm font-semibold px-6 py-3 rounded-full hover:bg-green-500 transition-all duration-200 shadow-md"
          >
            Avalúa tu propiedad gratis
          </router-link>
          <router-link
            to="/feed"
            class="flex items-center justify-center w-full sm:w-56 border border-white/40 text-white text-sm font-semibold px-6 py-3 rounded-full hover:bg-white/10 transition-all duration-200"
          >
            Explorar propiedades
          </router-link>
        </div>

        <!-- Stats -->
        <div class="flex flex-col sm:flex-row gap-4 sm:gap-8 lg:gap-10">
          <div class="flex flex-col gap-0.5">
            <span class="text-white text-xl lg:text-2xl font-bold"
              >53.000+</span
            >
            <span class="text-white/40 text-xs">propiedades analizadas</span>
          </div>
          <div class="flex flex-col gap-0.5">
            <span class="text-white text-xl lg:text-2xl font-bold"
              >&lt;11%</span
            >
            <span class="text-white/40 text-xs">error medio del avalúo</span>
          </div>
          <div class="flex flex-col gap-0.5">
            <span class="text-white text-xl lg:text-2xl font-bold">Gratis</span>
            <span class="text-white/40 text-xs">sin agentes, sin comisión</span>
          </div>
        </div>
      </div>

      <!-- Right: image -->
      <div class="hidden md:block flex-1 relative">
        <img
          src="@/assets/landing_cover.png"
          alt="Edificio residencial moderno"
          class="absolute inset-0 w-full h-full object-cover object-center rounded-r-3xl"
        />
      </div>
    </div>

    <!-- Cómo funciona — carousel -->
    <div class="mt-16 mb-8 flex flex-col gap-2">
      <span
        class="text-brand-muted text-xs font-semibold uppercase tracking-widest"
        >Cómo funciona</span
      >
      <h2 class="text-brand-text text-2xl lg:text-3xl font-bold">
        No somos un marketplace más.
      </h2>
      <p class="text-brand-muted text-sm lg:text-base max-w-lg leading-relaxed">
        Te ayudamos a decidir con datos reales, no con anuncios destacados.
      </p>
    </div>

    <Carousel
      v-model="currentSlide"
      :items-to-show="1.2"
      :wrap-around="true"
      snap-align="center"
      :autoplay="20000"
      :transition="600"
      class="mb-16"
    >
      <Slide v-for="(step, i) in howItWorks" :key="i">
        <div
          class="mx-3 rounded-3xl p-10 flex flex-col justify-between text-left w-full overflow-hidden relative transition-all duration-500 min-h-[260px]"
          :class="
            currentSlide === i
              ? 'bg-brand-dark opacity-100 scale-100'
              : 'bg-brand-dark opacity-30 scale-95'
          "
        >
          <div class="flex flex-col gap-3 relative z-10">
            <span
              class="text-brand-primary text-xs font-semibold uppercase tracking-widest"
              >Paso {{ i + 1 }}</span
            >
            <h3 class="text-white text-2xl font-bold leading-snug">
              {{ step.title }}
            </h3>
            <p class="text-white/60 text-sm leading-relaxed max-w-sm">
              {{ step.body }}
            </p>
          </div>
          <span
            class="text-white/5 font-black absolute bottom-2 right-4 leading-none select-none"
            style="font-size: 8rem"
            >0{{ i + 1 }}</span
          >
        </div>
      </Slide>
    </Carousel>

    <!-- Section header -->
    <div class="mt-16 mb-8 flex flex-col gap-1">
      <span
        class="text-brand-muted text-xs font-semibold uppercase tracking-widest"
        >Nuestros servicios</span
      >
      <h2 class="text-brand-text text-2xl lg:text-3xl font-bold">
        Todo lo que necesitas<br class="hidden sm:block" />para tu próxima
        decisión.
      </h2>
      <p class="text-brand-muted text-sm lg:text-base max-w-lg leading-relaxed">
        Decisiones respaldadas por datos reales de mercado, barrio y entorno.
      </p>
    </div>

    <!-- Bento grid: qué hacemos -->
    <div
      class="mt-8 flex flex-col md:grid md:gap-4"
      style="
        grid-template-columns: repeat(5, 1fr);
        grid-template-rows: repeat(5, 80px);
      "
    >
      <!-- AVM — grande izquierda arriba -->
      <div
        class="rounded-3xl bg-brand-dark p-8 flex flex-col justify-between overflow-hidden relative mb-4 md:mb-0 min-h-[200px]"
        style="grid-area: 1 / 1 / 4 / 4"
      >
        <div class="flex flex-col gap-2">
          <span
            class="text-brand-primary text-xs font-semibold uppercase tracking-widest"
            >Avalúo inteligente</span
          >
          <h3 class="text-white text-2xl font-bold leading-snug">
            Conoce el valor real<br />de tu propiedad
          </h3>
          <p class="text-white/50 text-sm max-w-xs leading-relaxed">
            Modelo entrenado con más de 53.000 propiedades. Resultado
            instantáneo, sin agentes.
          </p>
        </div>
        <span
          class="text-white/10 text-8xl font-black absolute bottom-4 right-6 leading-none select-none"
          >AVM</span
        >
      </div>

      <!-- Publicar — derecha arriba -->
      <div
        class="rounded-3xl bg-brand-primary p-8 flex flex-col justify-between mb-4 md:mb-0 min-h-[160px]"
        style="grid-area: 1 / 4 / 3 / 6"
      >
        <span
          class="text-white/70 text-xs font-semibold uppercase tracking-widest"
          >Para propietarios</span
        >
        <div class="flex flex-col gap-1">
          <h3 class="text-white text-xl font-bold">
            Publica gratis.<br />Sin comisión.
          </h3>
          <p class="text-white/70 text-xs leading-relaxed">
            Tu propiedad frente a miles de compradores e inquilinos reales.
          </p>
        </div>
      </div>

      <!-- Barrios / POIs — derecha abajo -->
      <div
        class="rounded-3xl bg-brand-text p-8 flex flex-col justify-between mb-4 md:mb-0 min-h-[200px]"
        style="grid-area: 3 / 4 / 6 / 6"
      >
        <span
          class="text-white/40 text-xs font-semibold uppercase tracking-widest"
          >Datos de barrios</span
        >
        <div class="flex flex-col gap-1">
          <h3 class="text-white text-xl font-bold">
            Conoce el barrio<br />antes de decidir
          </h3>
          <p class="text-white/50 text-xs leading-relaxed">
            Restaurantes, parques, transporte y más — todo georeferenciado.
          </p>
        </div>
      </div>

      <!-- Feed / búsqueda — grande izquierda abajo -->
      <div
        class="rounded-3xl bg-brand-primary-light p-8 flex flex-col justify-between overflow-hidden relative min-h-[160px]"
        style="grid-area: 4 / 1 / 6 / 4"
      >
        <span
          class="text-brand-primary text-xs font-semibold uppercase tracking-widest"
          >Búsqueda personalizada</span
        >
        <div class="flex flex-col gap-1">
          <h3 class="text-brand-text text-xl font-bold">
            Propiedades que se<br />adaptan a lo que buscas
          </h3>
          <p class="text-brand-muted text-xs leading-relaxed">
            Filtrá por barrio, tipo, precio y dejá que el onboarding haga el
            resto.
          </p>
        </div>
        <span
          class="text-brand-primary/10 text-8xl font-black absolute bottom-2 right-4 leading-none select-none"
          >→</span
        >
      </div>
    </div>

    <!-- CTA de cierre -->
    <div
      class="mt-16 w-full rounded-3xl overflow-hidden relative px-10 py-16 flex flex-col items-center text-center gap-6"
      style="
        background: radial-gradient(
            circle at 50% 35%,
            rgba(34, 197, 94, 0.14),
            transparent 55%
          ),
          #0b2f2a;
      "
    >
      <span
        class="text-brand-primary text-xs font-semibold uppercase tracking-widest"
        >Empieza ahora</span
      >
      <h2
        class="text-white text-3xl lg:text-4xl font-bold leading-tight max-w-lg"
      >
        Encuentra, compara y decide<br />con datos reales.
      </h2>
      <p class="text-white/60 text-sm lg:text-base max-w-sm leading-relaxed">
        Configurá tu búsqueda en 2 minutos. Gratis, sin agentes y sin comisión.
      </p>
      <div class="flex flex-col sm:flex-row gap-4">
        <router-link
          to="/register"
          class="w-full sm:w-56 text-center bg-brand-primary text-white text-sm font-semibold px-6 py-3 rounded-full hover:bg-green-500 transition-all duration-200 shadow-md"
        >
          Empezar gratis
        </router-link>
        <router-link
          to="/feed"
          class="w-full sm:w-56 border border-white/30 text-white text-sm font-semibold px-6 py-3 rounded-full hover:bg-white/10 transition-all duration-200"
        >
          Explorar propiedades
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Carousel, Slide } from "vue3-carousel";
import "vue3-carousel/dist/carousel.css";

const currentSlide = ref(0);

const howItWorks = [
  {
    title: "Dinos qué buscas",
    body: "Nada de scroll infinito. Cuéntanos qué querés y filtramos por tí. Barrio, tipo, presupuesto — una sola vez.",
  },
  {
    title: "Solo lo que te sirve",
    body: "Tu feed es tuyo — construido con lo que nos dijiste, no con lo que paga más pauta.",
  },
  {
    title: "Conoce el barrio antes de decidir",
    body: "Restaurantes, parques, transporte, colegios. Toda la info del entorno antes de dar el paso. Porque la propiedad es la mitad de la decisión.",
  },
];
</script>
