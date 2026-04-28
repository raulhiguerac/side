import { createApp } from "vue";
import { createPinia } from "pinia"; // 👈 Importamos Pinia
import App from "./App.vue";
import router from "./router";
import VueCookies from "vue3-cookies";
import { initializeApp } from "firebase/app";
import "./assets/tailwind.css";
import "./main.css";

const pinia = createPinia();

// initializeApp(firebaseConfig);
createApp(App).use(pinia).use(router).use(VueCookies).mount("#app");
