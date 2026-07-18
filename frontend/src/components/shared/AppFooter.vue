<template>
  <footer class="bg-brand-dark mt-4 px-[5%] sm:px-[8%] lg:px-[10%] py-12">
    <div class="flex flex-col md:flex-row justify-between gap-10">
      <!-- Brand -->
      <div class="flex flex-col gap-3 max-w-xs">
        <img src="@/assets/logo.svg" alt="Logo" class="h-8 w-fit" />
        <p class="text-white/55 text-xs leading-relaxed">
          El marketplace inmobiliario que pone los datos a tu favor. Bogotá,
          Colombia.
        </p>
      </div>

      <!-- Links -->
      <div class="flex flex-wrap gap-12">
        <div class="flex flex-col gap-3">
          <span
            class="text-white/30 text-xs font-semibold uppercase tracking-widest"
            >Producto</span
          >
          <div class="flex flex-col gap-2">
            <router-link
              to="/register"
              class="text-white/70 text-sm hover:text-white transition-colors"
              >Crear cuenta</router-link
            >
            <router-link
              to="/login"
              class="text-white/70 text-sm hover:text-white transition-colors"
              >Iniciar sesión</router-link
            >
            <a
              href="#"
              class="text-white/70 text-sm hover:text-white transition-colors"
              >Avalúa tu propiedad</a
            >
          </div>
        </div>
        <div class="flex flex-col gap-3">
          <span
            class="text-white/30 text-xs font-semibold uppercase tracking-widest"
            >Empresa</span
          >
          <div class="flex flex-col gap-2">
            <a
              href="#"
              class="text-white/70 text-sm hover:text-white transition-colors"
              >Sobre nosotros</a
            >
            <a
              href="#"
              class="text-white/70 text-sm hover:text-white transition-colors"
              >Contacto</a
            >
          </div>
        </div>
        <div class="flex flex-col gap-3">
          <span
            class="text-white/30 text-xs font-semibold uppercase tracking-widest"
            >Legal</span
          >
          <div class="flex flex-col gap-2">
            <a
              href="#"
              class="text-white/70 text-sm hover:text-white transition-colors"
              >Términos de uso</a
            >
            <a
              href="#"
              class="text-white/70 text-sm hover:text-white transition-colors"
              >Privacidad</a
            >
          </div>
        </div>
      </div>
    </div>

    <div
      class="border-t border-white/10 mt-10 pt-6 flex flex-col sm:flex-row justify-between items-center gap-2"
    >
      <span class="text-white/40 text-xs"
        >© 2026 Side. Todos los derechos reservados.</span
      >
      <span class="text-white/40 text-xs">Hecho en Bogotá 🇨🇴</span>
    </div>
  </footer>
</template>
