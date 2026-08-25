import type { BulkJobStatus } from "@/types/admin";

export const BULK_JOB_STATUS_LABELS: Record<BulkJobStatus, string> = {
  pending: "En curso",
  completed: "Completo",
  failed: "Fallido",
};

export const BULK_JOB_STATUS_BADGE_CLASSES: Record<BulkJobStatus, string> = {
  pending: "bg-orange-500 text-white",
  completed: "bg-green-500 text-white",
  failed: "bg-red-500 text-white",
};
