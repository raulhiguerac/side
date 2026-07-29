import type { ListingStatus } from "@/types/feed";
import type { VerificationStatus } from "@/types/properties";

/**
 * Fila de `GET /v1/admin/properties`. No es `PropertyCard`: esa es la tarjeta
 * pública del feed y esconde justo los campos con los que trabaja moderación
 * (`verification_status`, `owner_id`, `created_at`, `rejection_reason`).
 *
 * `price`, `area_m2` y `bathrooms` llegan como **string**: son `Decimal` en el
 * backend y pydantic los serializa así para no perder precisión.
 */
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
