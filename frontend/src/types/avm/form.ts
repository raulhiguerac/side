import type { SelectedPlace } from "@/types/maps/base";

export interface AvmFormState {
  property_type: "apartment" | "house";
  area_m2: number | null;
  bedrooms: number;
  bathrooms: number;
  parking_spots: number;
  stratum: number;
  year_built: number | null;
}

export interface AvmFormPayload {
  property_type: "apartment" | "house";
  area_m2: number;
  bedrooms: number;
  bathrooms: number;
  parking_spots: number;
  stratum: number;
  year_built: number | null;
}

export type AvmStepperKey = "bedrooms" | "bathrooms" | "parking_spots";

export interface AvmSubmitEvent {
  payload: AvmFormPayload;
  place: SelectedPlace;
  neighborhood: string;
}
