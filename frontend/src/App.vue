<template>
  <NavBar v-if="!$route.meta.hideNavbar" :links="links" />
  <router-view></router-view>
</template>

<script lang="ts" setup>
import NavBar from "@/components/NavBar.vue";
const links = [
  { names: "Home", router: "/" },
  { names: "About", router: "/about" },
  { names: "Login", router: "/login" },
  { names: "Register", router: "/register" },
];
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
