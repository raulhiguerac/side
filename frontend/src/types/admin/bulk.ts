export type BulkJobStatus = "pending" | "completed" | "failed";

/** Una fila fallida del CSV: `ref` es el `external_id`, o la línea si venía vacío. */
export interface BulkJobRowError {
  line: number;
  ref: string;
  issues: string[];
}

/** Fila de `GET /admin/properties/bulk`: trae `error_count`, no los errores. */
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

/** `GET /admin/properties/bulk/{id}/status`: la fila más sus errores. */
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
