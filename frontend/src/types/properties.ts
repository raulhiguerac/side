import type { PropertyImageCard } from "@/types/feed";

export interface CreatePropertyForm {
  property_type: string;
  listing_type: string;
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

export interface PropertyLocationDetail {
  neighborhood_id: string;
  city_id: string;
  country_id: string;
  latitude: number;
  longitude: number;
}

export interface PropertyDetail {
  id: string;
  property_type: "house" | "apartment";
  listing_type: "sale" | "rent";
  condition: "new" | "used" | "remodeled";
  status: "draft" | "active" | "inactive" | "sold" | "rented";
  verification_status: "unverified" | "pending" | "verified" | "rejected";

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
