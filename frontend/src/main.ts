import { createApp } from "vue";
import { createPinia } from "pinia"; // 👈 Importamos Pinia
import App from "./App.vue";
import router from "./router";
import VueCookies from "vue3-cookies";
import Vueform from "@vueform/vueform";
import vueformConfig from "./../vueform.config";
import "@vueform/multiselect/themes/default.css";
import "./assets/tailwind.css";
import "./main.css";

const pinia = createPinia();

createApp(App)
  .use(pinia)
  .use(router)
  .use(VueCookies)
  .use(Vueform, vueformConfig)
  .mount("#app");
