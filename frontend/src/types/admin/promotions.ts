import type { PropertyCard } from "@/types/feed";

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
