import type { Component } from "vue";
import type { OrsProfile } from "@/types/pois/base";

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

export interface RangeGroup {
  profile: OrsProfile;
  minutes: number;
  seconds: number;
  dot: string;
  count: number;
  pois: ReachablePoiItem[];
  isochrone: GeoJsonPolygon | null;
}

export interface CategoryGroup {
  label: string;
  icon: Component;
  pois: ReachablePoiItem[];
}

export interface RangeWithGroups extends RangeGroup {
  groups: CategoryGroup[];
}
