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

/** Los filtros que acepta `GetBulkJobsAdminRequest`; las fechas todavía no se exponen. */
export interface BulkJobsFilters {
  status?: string;
  has_errors?: string;
}
