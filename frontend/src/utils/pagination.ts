import type { PageRange } from "@/types/shared/pagination";

// Posición 1-based de los ítems visibles; {0, 0} si la página viene vacía.
export function pageRange(
  page: number,
  pageSize: number,
  shown: number
): PageRange {
  if (!shown) return { from: 0, to: 0 };
  const from = (page - 1) * pageSize + 1;
  return { from, to: from + shown - 1 };
}
