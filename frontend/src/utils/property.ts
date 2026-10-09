import {
  LISTING_TYPE_LABELS,
  PROPERTY_TYPE_LABELS,
} from "@/constants/propertyLabels";
import type { ListingType, PropertyType } from "@/types/properties/base";

// "Apartamento en venta"
export const propertyTitle = (type: PropertyType, listing: ListingType) =>
  `${PROPERTY_TYPE_LABELS[type]} en ${LISTING_TYPE_LABELS[
    listing
  ].toLowerCase()}`;
