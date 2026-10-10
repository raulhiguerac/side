import {
  LISTING_TYPE_LABELS,
  PROPERTY_TYPE_LABELS,
} from "@/constants/propertyLabels";
import type { PropertyCard } from "@/types/feed/cards";
import type { ListingType, PropertyType } from "@/types/properties/base";

// "Apartamento en venta"
export const propertyTitle = (type: PropertyType, listing: ListingType) =>
  `${PROPERTY_TYPE_LABELS[type]} en ${LISTING_TYPE_LABELS[
    listing
  ].toLowerCase()}`;

export function cityIdsOf(cards: PropertyCard[]): string[] {
  const ids = cards.flatMap((c) =>
    c.location?.city_id ? [c.location.city_id] : []
  );
  return [...new Set(ids)];
}
