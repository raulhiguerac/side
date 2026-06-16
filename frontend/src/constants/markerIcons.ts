import type { Component } from "vue";
import type { MarkerImageType } from "@/types/maps";
import {
  MapPinHouse,
  Building,
  ChefHat,
  NotebookPen,
  HeartPulse,
  Bus,
  ShoppingCart,
  MapPin,
} from "@lucide/vue";

export const markerIconMap: Record<MarkerImageType, Component> = {
  house: MapPinHouse,
  subject: MapPinHouse,
  apartment: Building,
  food: ChefHat,
  education: NotebookPen,
  health: HeartPulse,
  transport: Bus,
  commerce: ShoppingCart,
  poi: MapPin,
};
