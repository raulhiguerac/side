import type { Component } from "vue";
import type { PropertyType, ListingType } from "@/types/properties/base";
import type { PropertyDetail } from "@/types/properties/detail";

export interface CreatePropertyForm {
  property_type: PropertyType | "";
  listing_type: ListingType | "";
  condition: string;
  currency: string;
  area_m2: number | null;
  bedrooms: number | null;
  bathrooms: number | null;
  parking_spots: number;
  price: number | null;
  admin_fee: number | null;
  floor_number: number | null;
  total_floors: number | null;
  description: string;
  year_built: number | null;
  stratum: number | null;
  location: {
    neighborhood_id: string;
    city_id: string;
    country_id: string;
    latitude: number | null;
    longitude: number | null;
  };
}

export interface PropertyEditForm {
  condition: PropertyDetail["condition"];
  currency: PropertyDetail["currency"];
  price: number;
  admin_fee: number | null;
  description: string;
}

/** Opción de un selector de tarjetas del formulario de creación. */
export interface ChoiceOption<V extends string> {
  value: V;
  label: string;
  desc?: string;
  icon: Component;
}

export interface NumericFieldOption {
  key: "area_m2" | "bedrooms" | "bathrooms";
  label: string;
  icon: Component;
  min: string;
  step: string;
  placeholder: string;
}
