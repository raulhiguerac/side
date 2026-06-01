export interface FeedPreferences {
  city_ids?: string[];
  neighborhood_ids?: string[];
  property_types?: string[];
}

export interface PropertyImageCard {
  url: string;
  is_cover: boolean;
  display_order: number;
}

export interface PropertyLocationCard {
  neighborhood_id: string;
  city_id: string;
  latitude: number | null;
  longitude: number | null;
}

export interface PropertyCard {
  id: string;
  property_type: "house" | "apartment";
  listing_type: "sale" | "rent";
  status: "draft" | "active" | "inactive" | "sold" | "rented";
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
