export type ListingStatus = "draft" | "active" | "inactive" | "sold" | "rented";

export interface PropertyCardUI {
  id: string;
  title: string;
  price: number;
  location: string;
  image?: string;
  type: "sale" | "rent";
  status?: ListingStatus;
  bedrooms: number;
  bathrooms: number;
  area: number;
  isFavorite?: boolean;
}

export interface FeedFilters {
  min_price?: number | null;
  max_price?: number | null;
  min_area_m2?: number | null;
  max_area_m2?: number | null;
  min_bathrooms?: number | null;
  bedrooms?: number | null;
}

export interface FeedPreferences {
  city_ids?: string[];
  neighborhood_ids?: string[];
  property_types?: string[];
}

export interface PropertyImageCard {
  id: string;
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

export interface FeedPage {
  items: PropertyCard[];
  next_cursor: string | null;
}

export interface PropertyCard {
  id: string;
  property_type: "house" | "apartment";
  listing_type: "sale" | "rent";
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

export type PageCache = Record<
  string,
  { items: PropertyCard[]; nextCursor: string | null }
>;

export interface BboxPayload {
  min_lat: number;
  max_lat: number;
  min_lon: number;
  max_lon: number;
  zoom: number;
}
