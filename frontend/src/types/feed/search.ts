import type { PropertyCard } from "@/types/feed/cards";
import type { FeedFilters, FeedPreferences } from "@/types/feed/filters";

export interface FeedPage {
  items: PropertyCard[];
  next_cursor: string | null;
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

export type FeedQuery = FeedPreferences & FeedFilters & { cursor?: string };

export interface FeedMapQuery {
  min_lat: number;
  max_lat: number;
  min_lon: number;
  max_lon: number;
  resolution: number;
}
