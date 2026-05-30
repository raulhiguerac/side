import type { Component } from "vue";
import type { MarkerImageType } from "@/types/maps";
import { MapPinHouse, Building, ChefHat, NotebookPen } from "@lucide/vue";

export const markerIconMap: Record<MarkerImageType, Component> = {
  house: MapPinHouse,
  subject: MapPinHouse,
  apartment: Building,
  food: ChefHat,
  education: NotebookPen,
};
