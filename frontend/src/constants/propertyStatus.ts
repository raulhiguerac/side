import type { ListingStatus } from "@/types/feed";

export const LISTING_STATUS_LABELS: Record<ListingStatus, string> = {
  draft: "Borrador",
  active: "Activa",
  inactive: "Inactiva",
  sold: "Vendida",
  rented: "Arrendada",
};

export const LISTING_STATUS_BADGE_CLASSES: Record<ListingStatus, string> = {
  draft: "bg-gray-400 text-white",
  active: "bg-green-500 text-white",
  inactive: "bg-gray-500 text-white",
  sold: "bg-blue-500 text-white",
  rented: "bg-purple-500 text-white",
};
