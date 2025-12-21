import { createRouter, createWebHashHistory, RouteRecordRaw } from "vue-router";
import HomeView from "../views/HomeView.vue";
// import AboutView from "@/views/AboutView.vue";
import { useCookies } from "vue3-cookies";
// Vue.use(VueCookies, { expires: '7d'});

const routes: Array<RouteRecordRaw> = [
  {
    path: "/",
    name: "home",
    component: HomeView,
    meta: {
      requiresAuth: false,
    },
  },
  {
    path: "/about",
    name: "about",
    component: () => import("../views/AboutView.vue"),
    meta: {
      requiresAuth: false,
    },
  },
  {
    path: "/login",
    name: "login",
    component: () => import("../views/LoginView.vue"),
    meta: {
      hideNavbar: true,
      isLogged: true,
    },
  },
  {
    path: "/register",
    name: "register",
    component: () => import("../views/RegisterView.vue"),
    meta: {
      hideNavbar: true,
      isLogged: true,
    },
  },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

router.beforeEach((to) => {
  const { cookies } = useCookies();
  const accesToken = cookies.get("token");
  if (to.matched.some((record) => record.meta.requiresAuth)) {
    // this route requires auth, check if logged in
    // if not, redirect to login page.
    if (accesToken == null) {
      return { name: "login" };
    }
  }
  if (to.matched.some((record) => record.meta.isLogged)) {
    if (accesToken) {
      return { name: "about" };
    }
  }
});

export default router;
