import type { ListingType, PropertyType } from "@/types/feed";

export const PROPERTY_TYPE_LABELS: Record<PropertyType, string> = {
  house: "Casa",
  apartment: "Apartamento",
};

export const LISTING_TYPE_LABELS: Record<ListingType, string> = {
  sale: "Venta",
  rent: "Arriendo",
};
