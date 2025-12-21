<template>
  <div class="mt-20"></div>
  <div class="grid grid-cols-4 justify-items-center">
    <HouseCard v-for="prop in properties" :key="prop.PropertyId" :="prop" />
  </div>
  <div>
    <MapUser />
  </div>
</template>

<script lang="ts" setup>
// import HouseCard from "@/components/HouseCard.vue";
import MapUser from "@/components/MapUser.vue";
import Properties from "@/types/properties";
import axios from "axios";
import { onMounted, ref } from "vue";

const properties = ref<Properties[]>([]);

const getProperties = async () => {
  await axios
    .get("http://localhost:8000/properties", {
      headers: {
        "Access-Control-Allow-Origin": "*",
      },
    })
    .then((response) => {
      properties.value = response.data;
    })
    .catch((error) => console.log(error));
};

onMounted(() => {
  getProperties();
});
</script>
