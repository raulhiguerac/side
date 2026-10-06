import { BULK_JOB_STATUS_LABELS } from "@/constants/bulkJobStatus";
import {
  LISTING_STATUS_LABELS,
  VERIFICATION_STATUS_LABELS,
} from "@/constants/propertyStatus";
import type { AdminFilterDefinition } from "@/types/admin/filters";

// Solo los enums: `owner_id` e `is_promoted` no van en select.
export const MODERATION_FILTERS: readonly AdminFilterDefinition[] = [
  {
    key: "verification_status",
    label: "Verificación",
    options: VERIFICATION_STATUS_LABELS,
    allLabel: "Todas",
  },
  {
    key: "status",
    label: "Estado",
    options: LISTING_STATUS_LABELS,
    allLabel: "Todos",
  },
];

// `has_errors` es bool en el backend; Pydantic parsea "true"/"false".
export const BULK_JOB_FILTERS: readonly AdminFilterDefinition[] = [
  {
    key: "status",
    label: "Estado",
    options: BULK_JOB_STATUS_LABELS,
    allLabel: "Todos",
  },
  {
    key: "has_errors",
    label: "Errores",
    options: { true: "Con errores", false: "Sin errores" },
    allLabel: "Todas",
  },
];
