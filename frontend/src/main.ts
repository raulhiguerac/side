import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import VueCookies from "vue3-cookies";
import { initializeApp } from "firebase/app";
import "./assets/tailwind.css";
import "./main.css";

const firebaseConfig = {
  apiKey: "AIzaSyCwOXXjrG1J7xvYL682Z-w2Um2W55zb18k",
  authDomain: "aerobic-lock-411104.firebaseapp.com",
  projectId: "aerobic-lock-411104",
  storageBucket: "aerobic-lock-411104.appspot.com",
  messagingSenderId: "989638113729",
  appId: "1:989638113729:web:ec04cfc0f6b8e6ad6f5740",
  measurementId: "G-07RPYZKH8W",
};

initializeApp(firebaseConfig);
createApp(App).use(router).use(VueCookies).mount("#app");
