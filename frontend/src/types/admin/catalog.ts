import type { Geometry } from "geojson";
import type { Bbox } from "@/types/maps/base";

/** Fila de `GET /v1/admin/neighborhoods`: `svg_path` y `bbox` vienen nulos si el barrio no tiene geometría. */
export interface NeighborhoodAdminRow {
  id: string;
  locality_id: string;
  code: string;
  name: string;
  is_active: boolean;
  has_geometry: boolean;
  svg_path: string | null;
  bbox: Bbox | null;
}

export interface NeighborhoodCoverage {
  with_geometry: number;
  total: number;
}

export interface NeighborhoodAdminPage {
  items: NeighborhoodAdminRow[];
  total_items: number;
  total_pages: number;
  current_page: number;
  items_per_page: number;
  coverage: NeighborhoodCoverage;
}

/** Filtros que acepta `ListNeighborhoodsAdminRequest`; llegan como string desde la URL. */
export interface NeighborhoodAdminFilters {
  locality_id?: string;
  is_active?: string;
  has_geometry?: string;
  search_term?: string;
}

/** `GET /v1/admin/neighborhoods/{id}`: GeoJSON simplificado (~1,1 m) y área sobre la geometría original. */
export interface NeighborhoodAdminDetail {
  id: string;
  locality_id: string;
  code: string;
  name: string;
  postal_code: string | null;
  latitude: number;
  longitude: number;
  is_active: boolean;
  geometry: Geometry | null;
  area_m2: number | null;
}

/** Un vecino de `GET /v1/admin/neighborhoods/geometries`, ya recortado al bbox pedido. */
export interface NeighborhoodGeometryItem {
  id: string;
  name: string;
  geometry: Geometry;
}

export type NeighborhoodAction = "edit" | "geometry" | "deactivate";
