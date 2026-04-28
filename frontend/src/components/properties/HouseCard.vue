<template>
  <div>
    <div
      class="w-full max-w-sm m-1 bg-white border border-gray-200 rounded-lg shadow dark:bg-white dark:border-gray-700"
    >
      <div class="flex flex-col">
        <img
          class="w-9/10 m-1 rounded-lg shadow-lg"
          src="@/assets/casa.jpeg"
          alt="Bonnie image"
        />
        <div class="w-full h-24 -translate-y-1/2 z-50">
          <!-- class="w-24 h-24 rounded-full -translate-y-1/2 z-50" -->
          <img
            class="float-left w-24 h-24 rounded-full"
            src="@/assets/nav-image.svg"
          />
          <div class="float-right mr-5 mt-11">
            <h3>{{ PropertyInfo.vendorname }}</h3>
            <a class="flex items-center space-x-1 rtl:space-x-reverse">
              <img src="@/assets/location-icon.png" />
              <span>{{ PropertyInfo.City }}</span>
              <div class="inline-block w-0.5 self-stretch bg-gray-300"></div>
              <h3 class="text-center">{{ PropertyInfo.Type }}</h3>
            </a>
          </div>
        </div>
        <div
          class="-mt-11 mx-2 border-t border-2 border-gray-200 flex-grow"
        ></div>
        <div class="grid grid-cols-4 grid-rows-1 content-around mt-4 h-10 mx-1">
          <div class="col-span-1">
            <a
              class="flex items-center justify-center space-x-1 rtl:space-x-reverse"
            >
              <img class="w-6 h-6" src="@/assets/m2.png" />
              <span>{{ PropertyInfo.Area }}&nbsp;m²</span>
            </a>
          </div>
          <div class="col-span-1">
            <a
              class="flex items-center justify-center space-x-1 rtl:space-x-reverse"
            >
              <img class="w-6 h-6" src="@/assets/bed_89977.png" />
              <span>{{ PropertyInfo.Bedrooms }}&nbsp;Hab.</span>
            </a>
          </div>
          <div class="col-span-1">
            <a
              class="flex items-center justify-center space-x-1 rtl:space-x-reverse"
            >
              <img class="w-6 h-6" src="@/assets/bathroom.png" />
              <span>{{ PropertyInfo.Bathrooms }}&nbsp;Baños</span>
            </a>
          </div>
          <div class="col-span-1">
            <a
              class="flex items-center space-x-1 justify-center rtl:space-x-reverse"
            >
              <img class="w-6 h-6" src="@/assets/parking.png" />
              <span>{{ PropertyInfo.Garages }}&nbsp;Parq.</span>
            </a>
          </div>
        </div>
        <div class="flex mt-3 mx-3 mb-4">
          <a
            class="flex items-center space-x-1 justify-center rtl:space-x-reverse"
          >
            <img class="w-6 h-6" src="@/assets/casa-jogo-p.png" />
            <span class="text-md">{{ PropertyInfo.Neighborhood }}</span>
          </a>
          <div class="grow"></div>
          <h2 class="text-2xl">$&nbsp;{{ PropertyInfo.Price }}</h2>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import Properties from "@/types/properties";
// import { PropType } from "vue";
// eslint-disable-next-line @typescript-eslint/no-unused-vars
// const props = defineProps({
//   properties: { type: Object as PropType<Properties>, required: true },
// });
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const props = defineProps<Properties>();
</script>
