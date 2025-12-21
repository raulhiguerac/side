<template>
  <div class="m-auto w-[90vw] h-[60vh] flex">
    <div class="w-1/4 h-full mx-1">
      <!-- <input
        v-model="adress"
        type="text"
        class="border border-gray-400 py-1 px-2 w-full rounded-lg h-11"
        placeholder="Dirección"
        required
      /> -->
      <vue-google-autocomplete
        v-model="adress"
        id="map"
        class="border border-gray-400 py-1 px-2 w-full rounded-lg h-11"
        classname="form-control"
        placeholder="Start typing"
        v-on:placechanged="getAddressData"
        country="co"
      >
      </vue-google-autocomplete>
      <div class="h-5">{{ adress }}</div>
    </div>
    <div class="w-3/4 h-full mx-1">
      <l-map ref="map" v-model:zoom="zoom" :center="[lat, lon]">
        <l-tile-layer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          layer-type="base"
          name="OpenStreetMap"
        ></l-tile-layer>
        <l-marker :lat-lng="[lat, lon]"></l-marker>
      </l-map>
    </div>
  </div>
</template>

<script lang="ts" setup>
import "leaflet/dist/leaflet.css";
import { LMap, LTileLayer, LMarker } from "@vue-leaflet/vue-leaflet";
import { onMounted, ref, watchEffect } from "vue";
import VueGoogleAutocomplete from "vue-google-autocomplete";

let lat = ref(4.624335);
let lon = ref(-74.063644);
const zoom = 16;

const adress = ref("");

const getLocation = async () => {
  if (localStorage.getItem("latitude") && localStorage.getItem("longitude")) {
    lat.value = +localStorage.getItem("latitude");
    lon.value = +localStorage.getItem("longitude");
  } else {
    let navData = await navigator.geolocation;
    if (navData) {
      navigator.geolocation.getCurrentPosition((position) => {
        localStorage.setItem("latitude", position.coords.latitude);
        localStorage.setItem("longitude", position.coords.longitude);
        lat.value = position.coords.latitude;
        lon.value = position.coords.longitude;
      });
    }
  }
};

const getAddressData = function (addressData, placeResultData, id) {
  adress.value = addressData;
  localStorage.setItem("latitude", addressData.latitude);
  localStorage.setItem("longitude", addressData.longitude);
  lat.value = addressData.latitude;
  lon.value = addressData.longitude;
};

onMounted(() => {
  getLocation();
});

watchEffect(() => {
  getLocation();
  console.log("cambio lat lon");
  console.log(lat.value, lon.value);
  console.log(adress.value);
});
</script>
