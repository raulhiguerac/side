import type { Component } from "vue";
import type { MarkerImageType } from "@/types/maps";
import {
  School,
  HeartPulse,
  ShoppingCart,
  Bus,
  Croissant,
  Utensils,
  Landmark,
  TreePine,
} from "@lucide/vue";

export type OrsProfile = "foot-walking" | "cycling-regular" | "driving-car";

export interface ProfileOption {
  key: OrsProfile;
  label: string;
  icon: Component;
  description: string;
}

export interface ReachablePoiItem {
  name: string;
  category: string | null;
  latitude: number;
  longitude: number;
  full_address: string | null;
  phone: string | null;
  website: string | null;
}

export interface ReachablePoisResult {
  profile: OrsProfile;
  range: number | null;
  isochrone: GeoJsonPolygon | null;
  pois: ReachablePoiItem[];
  error: string | null;
}

export interface GeoJsonPolygon {
  type: "Polygon";
  coordinates: number[][][];
}

export const CATEGORY_PRIORITY: Record<string, number> = {
  // Salud
  hospital: 1,
  clinic: 1,
  doctor: 1,
  dentist: 1,
  pharmacy: 1,
  // Educación
  school: 2,
  kindergarten: 2,
  college: 2,
  university: 2,
  // Restaurantes
  restaurant: 3,
  cafe: 3,
  fast_food: 3,
  // Mercados
  supermarket: 4,
  convenience: 4,
  // Resto
  bus_station: 5,
  platform: 5,
  stop_position: 5,
  bakery: 6,
  bank: 7,
  atm: 7,
  park: 8,
  fitness_centre: 8,
};

export const PRIORITY_CATEGORIES = new Set(Object.keys(CATEGORY_PRIORITY));

export interface CategoryMeta {
  label: string;
  icon: Component;
  bucket: MarkerImageType;
}

export const CATEGORY_META: Record<string, CategoryMeta> = {
  school: { label: "Educación", icon: School, bucket: "education" },
  kindergarten: { label: "Educación", icon: School, bucket: "education" },
  college: { label: "Educación", icon: School, bucket: "education" },
  university: { label: "Educación", icon: School, bucket: "education" },
  hospital: { label: "Salud", icon: HeartPulse, bucket: "health" },
  clinic: { label: "Salud", icon: HeartPulse, bucket: "health" },
  doctor: { label: "Salud", icon: HeartPulse, bucket: "health" },
  dentist: { label: "Salud", icon: HeartPulse, bucket: "health" },
  pharmacy: { label: "Salud", icon: HeartPulse, bucket: "health" },
  supermarket: {
    label: "Supermercados",
    icon: ShoppingCart,
    bucket: "commerce",
  },
  bus_station: { label: "Transporte", icon: Bus, bucket: "transport" },
  platform: { label: "Transporte", icon: Bus, bucket: "transport" },
  stop_position: { label: "Transporte", icon: Bus, bucket: "transport" },
  bakery: { label: "Panadería", icon: Croissant, bucket: "food" },
  convenience: { label: "Tienda", icon: ShoppingCart, bucket: "commerce" },
  restaurant: { label: "Restaurantes", icon: Utensils, bucket: "food" },
  cafe: { label: "Cafés", icon: Utensils, bucket: "food" },
  fast_food: { label: "Comida rápida", icon: Utensils, bucket: "food" },
  bank: { label: "Banco", icon: Landmark, bucket: "poi" },
  atm: { label: "Banco", icon: Landmark, bucket: "poi" },
  park: { label: "Parques", icon: TreePine, bucket: "poi" },
  fitness_centre: { label: "Gimnasio", icon: TreePine, bucket: "poi" },
};

export interface RangeGroup {
  profile: OrsProfile;
  minutes: number;
  seconds: number;
  dot: string;
  count: number;
  pois: ReachablePoiItem[];
  isochrone: GeoJsonPolygon | null;
}
