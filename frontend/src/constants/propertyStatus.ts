import type { ListingStatus } from "@/types/feed";
import type { VerificationStatus } from "@/types/properties";

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

export const VERIFICATION_STATUS_LABELS: Record<VerificationStatus, string> = {
  unverified: "Sin verificar",
  pending: "Pendiente",
  verified: "Verificada",
  rejected: "Rechazada",
};

export const VERIFICATION_STATUS_BADGE_CLASSES: Record<
  VerificationStatus,
  string
> = {
  unverified: "bg-gray-400 text-white",
  pending: "bg-orange-500 text-white",
  verified: "bg-green-500 text-white",
  rejected: "bg-red-500 text-white",
};
