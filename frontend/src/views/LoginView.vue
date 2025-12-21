<template>
  <div class="min-h-screen py-40 bg-[#50d71e]">
    <div class="container mx-auto">
      <div
        class="flex flex-col lg:flex-row w-8/12 border bg-white rounded-xl mx-auto shadow-lg overflow-hidden"
      >
        <div class="w-full lg:w-1/2 bg-[#1D1D35]">
          <div class="h-3/4">
            <img
              class="flex justify-center items-center lg:w-full lg:h-full"
              src="@/assets/trace (1).svg"
            />
          </div>
          <div
            class="h-1/4 flex flex-col items-center justify-center p-4 text-center"
          >
            <p class="text-white">
              Compra, vende o arrienda tu propiedad soñada en minutos
            </p>
          </div>
        </div>
        <div class="w-full lg:w-1/2 py-16 px-12">
          <h2 class="text-3xl mb-4">Inicia sesión</h2>
          <form>
            <div class="mt-5">
              <label for="inputnumber1">Correo</label>
            </div>
            <input
              v-model="user.email"
              type="text"
              class="border border-gray-400 py-1 px-2 w-full rounded-lg h-11"
              placeholder="Número telefónico"
            />
            <div class="mt-5">
              <label for="inputnumber1">Contraseña</label>
            </div>
            <div class="relative">
              <input
                v-model="user.password"
                :type="showPassword ? 'text' : 'password'"
                class="border border-gray-400 py-1 px-2 w-full rounded-lg h-11"
                placeholder="Número telefónico"
              />
              <button
                class="absolute top-0 end-0 p-3.5 rounded-e-md"
                @click.prevent="hidePassword"
              >
                <svg
                  class="flex-shrink-0 size-3.5 text-gray-400 dark:text-neutral-600"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path
                    :class="{ hidden: showPassword, block: !showPassword }"
                    d="M9.88 9.88a3 3 0 1 0 4.24 4.24"
                  ></path>
                  <path
                    :class="{ hidden: showPassword, block: !showPassword }"
                    d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"
                  ></path>
                  <path
                    :class="{ hidden: showPassword, block: !showPassword }"
                    d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"
                  ></path>
                  <line
                    :class="{ hidden: showPassword, block: !showPassword }"
                    x1="2"
                    x2="22"
                    y1="2"
                    y2="22"
                  ></line>
                  <path
                    :class="{ hidden: !showPassword, block: showPassword }"
                    d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"
                  ></path>
                  <circle
                    :class="{ hidden: !showPassword, block: showPassword }"
                    cx="12"
                    cy="12"
                    r="3"
                  ></circle>
                </svg>
              </button>
            </div>
          </form>
          <button
            class="w-full mt-5 border py-1 px-2 rounded-lg h-11 bg-[#08bc6c] text-white font-bold hover:shadow disabled:bg-gray-300 disabled:cursor-not-allowed disabled:opacity-50 disabled:text-[#3A414A]"
            :disabled="isDisabled"
            @click.prevent="accessUser"
          >
            Iniciar sesión
          </button>
          <div class="flex items-center mt-5">
            <div class="border-t border-2 border-gray-200 flex-grow"></div>
            <div class="px-3 text-gray-800 text-sm font-thin">
              O iniciar sesión con
            </div>
            <div class="border-t border-2 border-gray-200 flex-grow"></div>
          </div>
          <!-- <button class="flex mt-5 w-full space-x-2 px-4 py-2 border rounded-lg justify-center border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:border-slate-400 dark:hover:border-slate-500 hover:text-slate-900 dark:hover:text-slate-300 hover:shadow transition duration-150" @click.prevent="signInWithGoogle"> -->
          <button
            class="flex mt-5 w-full space-x-2 px-4 py-2 justify-center border rounded-lg>"
            @click.prevent="prueba"
          >
            <img
              class="w-6 h-6"
              src="https://www.svgrepo.com/show/475656/google-color.svg"
              loading="lazy"
              alt="google logo"
            />
            <span class="text-center font-medium">Google</span>
          </button>
          <p class="mt-5 text-sm font-light text-gray-500 dark:text-gray-400">
            Aún no tienes cuenta?
            <a
              href="#"
              class="font-medium text-primary-600 hover:underline dark:text-primary-500"
              >Registrarse</a
            >
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed } from "vue";
import { useVuelidate } from "@vuelidate/core";
import { required, email } from "vuelidate/lib/validators";
import axios from "axios";
import router from "../router";
import { getAuth, signInWithPopup, GoogleAuthProvider } from "firebase/auth";

let user = ref({
  email: "",
  password: "",
});

const validations = {
  email: { required, email },
  password: { required },
};

const v$ = useVuelidate(validations, user);

const isDisabled = computed(() => {
  return v$.value.$invalid;
});

let showPassword = ref(false);

const hidePassword = function () {
  showPassword.value = !showPassword.value;
};

const accessUser = async () => {
  await axios
    .post(
      "http://localhost:8000/login",
      {
        Email: user.value.email,
        Password: user.value.password,
      },
      { withCredentials: true }
    )
    .then((response) => {
      console.log(response.data);
      console.log(response.status);
      if (response.status === 200) {
        router.push("/");
      }
    })
    .catch((error) => {
      console.log(error);
    });
};

const signInWithGoogle = async () => {
  const provider = new GoogleAuthProvider();
  provider.addScope("https://www.googleapis.com/auth/user.phonenumbers.read");
  provider.setCustomParameters({
    prompt: "select_account",
  });
  const auth = getAuth();
  const token = await signInWithPopup(auth, provider).then((result) => {
    const credential = GoogleAuthProvider.credentialFromResult(result);
    try {
      if (credential) {
        return result.user.providerData[0].uid;
      }
    } catch (error) {
      console.log(error);
    }
  });
  return token;
};

const prueba = async () => {
  const token = await signInWithGoogle();
  await axios
    .post(
      "http://localhost:8000/login/google",
      {
        Token: token,
      },
      { withCredentials: true }
    )
    .then((response) => {
      console.log(response.data);
      console.log(response.status);
      if (response.status === 200) {
        router.push("/");
      }
    })
    .catch((error) => {
      console.log(error);
    });
};

// export default class LoginView extends Vue {}
</script>
