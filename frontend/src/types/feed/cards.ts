import type {
  ListingStatus,
  PropertyType,
  ListingType,
} from "@/types/properties/base";
import type { PropertyImageCard } from "@/types/properties/images";

export interface PropertyLocationCard {
  neighborhood_id: string;
  city_id: string;
  latitude: number | null;
  longitude: number | null;
}

export interface PropertyCard {
  id: string;
  property_type: PropertyType;
  listing_type: ListingType;
  status: ListingStatus;
  price: number;
  currency: "COP" | "USD" | "EUR" | "MXN" | "PEN" | "CLP" | "ARS";
  area_m2: number;
  bedrooms: number;
  bathrooms: number;
  parking_spots: number;
  is_promoted: boolean;
  location: PropertyLocationCard | null;
  images: PropertyImageCard[];
}

export interface PropertyCardUI {
  id: string;
  title: string;
  price: number;
  location: string;
  image?: string;
  type: ListingType;
  status?: ListingStatus;
  bedrooms: number;
  bathrooms: number;
  area: number;
  isFavorite?: boolean;
}
