import type { PropertyCard } from "@/types/feed/cards";

/** Fila de `GET /admin/promotions`: la promoción con su property anidada. */
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
