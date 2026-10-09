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
