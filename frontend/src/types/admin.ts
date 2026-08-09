import type { ListingStatus } from "@/types/feed";
import type { PropertyDetail, VerificationStatus } from "@/types/properties";

/**
 * `GET /v1/admin/properties/{id}`: el detalle más los destinos legales desde el
 * estado en que está, que el backend calcula con la misma tabla que después aplica.
 */
export interface AdminPropertyDetail extends PropertyDetail {
  allowed_verification_targets: VerificationStatus[];
  allowed_status_targets: ListingStatus[];
}

/** Fila del listado admin: lleva los campos que `PropertyCard` esconde, y los `Decimal` llegan como string. */
export interface AdminPropertyRow {
  id: string;
  owner_id: string;
  property_type: "house" | "apartment";
  listing_type: "sale" | "rent";
  status: ListingStatus;
  verification_status: VerificationStatus;
  rejection_reason: string | null;
  price: string;
  currency: "COP" | "USD" | "EUR" | "MXN" | "PEN";
  area_m2: string;
  bedrooms: number;
  bathrooms: string;
  created_at: string;
}

export interface AdminPropertiesPage {
  items: AdminPropertyRow[];
  total: number;
  page: number;
  page_size: number;
}

/** Filtros que acepta `GetPropertiesAdminRequest` en el backend. */
export interface AdminPropertiesFilters {
  status?: ListingStatus;
  verification_status?: VerificationStatus;
  owner_id?: string;
}

/** Solo los campos que cambiaron; cada uno es su propio endpoint, así que son uno o dos requests. */
export interface ModerationPayload {
  verificationStatus?: VerificationStatus;
  /** Obligatorio si `verificationStatus` es `rejected`; prohibido si no. */
  rejectionReason?: string;
  status?: ListingStatus;
}
