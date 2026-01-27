<template>
  <div class="min-h-screen lg:h-screen flex flex-col lg:overflow-hidden">
    <NavBar v-if="!$route.meta.hideNavbar" :links="links" class="flex-none" />

    <main class="flex-1 min-h-0 overflow-y-auto lg:overflow-hidden">
      <router-view></router-view>
    </main>
  </div>
</template>

<script lang="ts" setup>
import { onMounted } from "vue";
import NavBar from "@/components/NavBar.vue";
import { useAuthStore } from "@/stores/auth";

// Links para el navbar (legacy, ya no se usan)
const links = [
  { names: "Home", router: "/" },
  { names: "About", router: "/about" },
  { names: "Login", router: "/login" },
  { names: "Register", router: "/register" },
];

// 🔐 Verificar autenticación al iniciar la app
const authStore = useAuthStore();

onMounted(async () => {
  // Solo verificamos una vez al cargar la app
  // Si hay cookie válida, el usuario quedará logueado
  await authStore.checkAuth();
});
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  /* text-align: center; */
  color: #2c3e50;
}

nav {
  padding: 30px;
}

nav a {
  font-weight: bold;
  color: #2c3e50;
}

nav a.router-link-exact-active {
  color: #42b983;
}
</style>
