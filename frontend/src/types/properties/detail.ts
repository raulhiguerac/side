import type {
  ListingStatus,
  PropertyType,
  ListingType,
  VerificationStatus,
} from "@/types/properties/base";
import type { PropertyImageCard } from "@/types/properties/images";

export interface PropertyLocationDetail {
  neighborhood_id: string;
  city_id: string;
  country_id: string;
  latitude: number;
  longitude: number;
}

export interface PropertyDetail {
  id: string;
  property_type: PropertyType;
  listing_type: ListingType;
  condition: "new" | "used" | "remodeled";
  status: ListingStatus;
  verification_status: VerificationStatus;

  price: number;
  currency: "COP" | "USD" | "EUR" | "MXN" | "PEN" | "CLP" | "ARS";
  admin_fee: number | null;

  area_m2: number;
  bedrooms: number;
  bathrooms: number;
  parking_spots: number;
  floor_number: number | null;
  total_floors: number | null;

  stratum: number | null;
  description: string | null;
  year_built: number | null;

  created_at: string;

  location: PropertyLocationDetail | null;
  images: PropertyImageCard[];
}
