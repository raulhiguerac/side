import type { PropertyCard } from "@/types/feed/cards";

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
