<template>
  <div class="min-h-screen py-40 bg-[#F5F7FA]">
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
          <h2 class="text-2xl mb-4 text-center">!Regístrate gratis!</h2>
          <div class="flex items-center justify-center space-x-4">
            <div class="w-10 h-1 rounded-md" :class="optionsClasses[0]"></div>
            <div class="w-10 h-1 rounded-md" :class="optionsClasses[1]"></div>
          </div>
          <form>
            <div v-if="step === 1" class="mt-5">
              <div class="flex grow space-x-6">
                <div>
                  <div>
                    <label>Nombres</label>
                  </div>
                  <input
                    v-model="user.name"
                    type="text"
                    class="border border-gray-400 py-1 px-2 w-full rounded-lg h-11"
                    placeholder="Nombre completo"
                    required
                  />
                  <p class="text-red-600 text-sm mt-1 min-h-[1.25rem]">
                    <span v-if="v1.name.$error">
                      El nombre es obligatorio
                    </span>
                  </p>
                </div>
                <div>
                  <div>
                    <label>Apellidos</label>
                  </div>
                  <input
                    v-model="user.lastName"
                    type="text"
                    class="border border-gray-400 py-1 px-2 w-full rounded-lg h-11"
                    placeholder="Apellidos"
                    required
                  />
                  <p class="text-red-600 text-sm mt-1 min-h-[1.25rem]">
                    <span v-if="v1.lastName.$error">
                      El apellido es obligatorio
                    </span>
                  </p>
                </div>
              </div>
              <div>
                <label>Celular</label>
              </div>
              <input
                v-model="user.phone"
                type="text"
                class="border border-gray-400 py-1 px-2 w-full rounded-lg h-11"
                placeholder="Número telefónico +57"
              />
              <p class="text-red-600 text-sm mt-1 min-h-[1.25rem]">
                <span v-if="v1.phone.$error">
                  El celular debe contener exactamente 10 digitos
                </span>
              </p>
              <button
                class="w-full mt-1 border py-1 px-2 rounded-lg h-11 bg-[#08bc6c] text-white font-bold hover:shadow disabled:bg-gray-300 disabled:cursor-not-allowed disabled:opacity-50 disabled:text-[#3A414A]"
                @click.prevent="nextPage"
              >
                Siguiente
              </button>
            </div>
            <div v-if="step === 2">
              <div class="mt-5">
                <label>Correo</label>
              </div>
              <input
                v-model="user.email"
                type="email"
                autocomplete="email"
                class="border border-gray-400 py-1 px-2 w-full rounded-lg h-11"
                placeholder="Correo electronico"
              />
              <p class="text-red-600 text-sm mt-1 min-h-[1.25rem]">
                <span v-if="v2.email.$error"> El correo debe ser valido </span>
              </p>
              <div>
                <label>Contraseña</label>
              </div>
              <div class="relative">
                <input
                  v-model="user.password"
                  :type="showPassword ? 'text' : 'password'"
                  class="border border-gray-400 py-1 px-2 w-full rounded-lg h-11"
                  placeholder="Contraseña"
                />
                <p
                  class="text-sm mt-1 min-h-[1.25rem]"
                  :class="passwordMessageClass"
                >
                  {{ passwordMessage || "" }}
                </p>
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
              <button
                class="w-full mt-1 border py-1 px-2 rounded-lg h-11 bg-[#08bc6c] text-white font-bold hover:shadow disabled:bg-gray-300 disabled:cursor-not-allowed disabled:opacity-50 disabled:text-[#3A414A]"
                :disabled="isDisabled"
                @click.prevent="registerUser"
              >
                ¡Regístrate gratis!
              </button>
            </div>
          </form>
          <div class="flex items-center mt-5">
            <div class="border-t border-2 border-gray-200 flex-grow"></div>
            <div class="px-3 text-gray-800 text-sm font-thin">
              O iniciar sesión con
            </div>
            <div class="border-t border-2 border-gray-200 flex-grow"></div>
          </div>
          <button
            class="flex mt-5 w-full space-x-2 px-4 py-2 justify-center border rounded-lg border-gray-400 hover:shadow cursor-pointer"
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
import {
  required,
  minLength,
  maxLength,
  numeric,
  email,
} from "vuelidate/lib/validators";
import axios from "axios";
import router from "../router";
import { getAuth, GoogleAuthProvider, signInWithPopup } from "firebase/auth";

const step = ref(1);

const optionsClasses = computed(() => {
  return [
    {
      "bg-[#08bc6c]": step.value === 1,
      "bg-gray-200": step.value !== 1,
    },
    {
      "bg-[#08bc6c]": step.value === 2,
      "bg-gray-200": step.value !== 2,
    },
  ];
});

let user = ref({
  name: "",
  lastName: "",
  phone: "",
  email: "",
  password: "",
});

const rulesStep1 = computed(() => ({
  name: { required },
  lastName: { required },
  phone: {
    required,
    minLength: minLength(10),
    maxLength: maxLength(10),
    numeric,
  },
}));

const rulesStep2 = computed(() => ({
  email: { required, email },
  password: { required, minLength: minLength(8) },
}));

const v1 = useVuelidate(rulesStep1, user);
const v2 = useVuelidate(rulesStep2, user);

const nextPage = async () => {
  v1.value.$touch();
  if (v1.value.$invalid) return;
  step.value = 2;
};

let showPassword = ref(false);

const hidePassword = function () {
  showPassword.value = !showPassword.value;
};

const PASSWORD_MIN_LENGTH = 8;

const passwordMessage = computed(() => {
  if (!user.value.password) {
    return null;
  }

  if (user.value.password.length < PASSWORD_MIN_LENGTH) {
    return `La contraseña debe tener al menos ${PASSWORD_MIN_LENGTH} caracteres`;
  }

  return "Contraseña válida";
});

const passwordMessageClass = computed(() => {
  if (!user.value.password) return "text-gray-400";
  if (user.value.password.length < PASSWORD_MIN_LENGTH) return "text-red-600";
  return "text-green-600";
});

const isDisabled = computed(() => {
  return v2.value.$invalid;
});

const registerUser = async () => {
  await axios
    .post(
      "http://localhost:8000/user/register",
      {
        Email: user.value.email,
        Password: user.value.password,
        Profile: {
          Name: user.value.name,
          LastName: user.value.lastName,
          PhoneNumber: user.value.phone,
        },
      },
      { withCredentials: true }
    )
    .then((response) => {
      console.log(response.data);
      console.log(response.status);
      if (response.status === 201) {
        router.push("/");
      }
    })
    .catch((error) => {
      console.log(error);
    });
};
</script>
