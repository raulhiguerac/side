import type { Component } from "vue";
import type { MarkerImageType } from "@/types/maps/base";

export type OrsProfile = "foot-walking" | "cycling-regular" | "driving-car";

export interface ProfileOption {
  key: OrsProfile;
  label: string;
  icon: Component;
  description: string;
}

export interface CategoryMeta {
  label: string;
  icon: Component;
  bucket: MarkerImageType;
}
