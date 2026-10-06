import type { ListingStatus, ListingType, PropertyType } from "@/types/feed";
import type { PropertyDetail, VerificationStatus } from "@/types/properties";

/** Detalle admin: el de la property más los destinos legales del backend. */
export interface AdminPropertyDetail extends PropertyDetail {
  allowed_verification_targets: VerificationStatus[];
  allowed_status_targets: ListingStatus[];
}

/** Fila del listado admin: lleva los campos que `PropertyCard` esconde, y los `Decimal` llegan como string. */
export interface AdminPropertyRow {
  id: string;
  owner_id: string;
  property_type: PropertyType;
  listing_type: ListingType;
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
  /** Por promoción activa: `false` deja solo las promocionables. */
  is_promoted?: boolean;
}
