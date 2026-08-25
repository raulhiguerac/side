import type { ListingStatus, PropertyCard } from "@/types/feed";
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
  /** Por promoción activa: `false` deja solo las promocionables. */
  is_promoted?: boolean;
}

/**
 * Fila de `GET /v1/admin/promotions`: la promoción, con la property adentro. No
 * es `PropertyCard` — esa solo sabe decir si está promocionada, no con qué
 * prioridad ni hasta cuándo.
 */
export interface AdminPromotionRow {
  id: string;
  property_id: string;
  priority: number;
  starts_at: string;
  ends_at: string;
  is_active: boolean;
  property: PropertyCard | null;
}

export interface AdminPromotionsPage {
  items: AdminPromotionRow[];
  total: number;
  page: number;
  page_size: number;
}

/** Lo que el formulario de promoción emite: el `property_id` lo pone quien lo ejecuta. */
export interface PromotionPayload {
  promotedDays: number;
  priority: number;
}

/** Solo los campos que cambiaron; cada uno es su propio endpoint, así que son uno o dos requests. */
export interface ModerationPayload {
  verificationStatus?: VerificationStatus;
  /** Obligatorio si `verificationStatus` es `rejected`; prohibido si no. */
  rejectionReason?: string;
  status?: ListingStatus;
}

/** Un filtro de `AdminFilterBar`: la `key` es el query param y el campo que espera
 * el backend, y `options` es el `{ value: label }` de `constants/propertyStatus.ts`. */
export interface AdminFilterDefinition {
  key: string;
  label: string;
  options: Readonly<Record<string, string>>;
  /** La opción que quita el filtro; "Todas" si no se pasa. */
  allLabel?: string;
}

export type BulkJobStatus = "pending" | "completed" | "failed";

/** Una fila fallida del CSV: `ref` es el `external_id`, o la línea si venía vacío. */
export interface BulkJobRowError {
  line: number;
  ref: string;
  issues: string[];
}

/** Fila de `GET /v1/admin/properties/bulk`: lleva `error_count` y no el array —
 * una corrida puede tirar miles, y el detalle lo sirve el endpoint de status. */
export interface BulkJobRow {
  id: string;
  job_type: "bulk_create_properties";
  status: BulkJobStatus;
  inserted: number;
  error_count: number;
  retry_of_job_id: string | null;
  storage_key: string;
  /** Cuando vence el CSV en storage; pasado eso no hay archivo que relanzar. */
  expires_at: string;
  created_at: string;
  created_by: string | null;
}

export interface BulkJobsPage {
  items: BulkJobRow[];
  total: number;
  page: number;
  page_size: number;
}

/** `GET /v1/admin/properties/bulk/{id}/status`: lo mismo que la fila, pero con
 * los errores adentro y sin lo que ya vino en el listado. */
export interface BulkJobStatusDetail {
  batch_id: string;
  status: BulkJobStatus;
  inserted: number;
  errors: BulkJobRowError[];
}
