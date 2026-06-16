import type { Component } from "vue";
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
}

export const CATEGORY_META: Record<string, CategoryMeta> = {
  school: { label: "Educación", icon: School },
  kindergarten: { label: "Educación", icon: School },
  college: { label: "Educación", icon: School },
  university: { label: "Educación", icon: School },
  hospital: { label: "Salud", icon: HeartPulse },
  clinic: { label: "Salud", icon: HeartPulse },
  doctor: { label: "Salud", icon: HeartPulse },
  dentist: { label: "Salud", icon: HeartPulse },
  pharmacy: { label: "Salud", icon: HeartPulse },
  supermarket: { label: "Supermercados", icon: ShoppingCart },
  bus_station: { label: "Transporte", icon: Bus },
  platform: { label: "Transporte", icon: Bus },
  stop_position: { label: "Transporte", icon: Bus },
  bakery: { label: "Panadería", icon: Croissant },
  convenience: { label: "Tienda", icon: ShoppingCart },
  restaurant: { label: "Restaurantes", icon: Utensils },
  cafe: { label: "Cafés", icon: Utensils },
  fast_food: { label: "Comida rápida", icon: Utensils },
  bank: { label: "Banco", icon: Landmark },
  atm: { label: "Banco", icon: Landmark },
  park: { label: "Parques", icon: TreePine },
  fitness_centre: { label: "Gimnasio", icon: TreePine },
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
