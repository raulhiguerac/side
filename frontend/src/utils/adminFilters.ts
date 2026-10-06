import type { LocationQuery } from "vue-router";
import type { CatalogItem } from "@/types/catalog";
import type {
  AdminFilterDefinition,
  AdminFilterOptions,
} from "@/types/admin/filters";

/** Deja solo las keys definidas y, en los selects fijos, solo valores del enum: la
 * query la escribe cualquiera, y `?status=banana` es un 422 del backend. */
export function sanitizeFilterQuery(
  query: LocationQuery,
  filters: readonly AdminFilterDefinition[]
): Record<string, string> {
  const clean: Record<string, string> = {};

  for (const filter of filters) {
    // Una key repetida llega como array: ahí no hay un valor único que aplicar.
    const value = query[filter.key];
    if (typeof value !== "string" || !value) continue;
    // Async y búsqueda no tienen enum que mirar: los valida el backend.
    if (
      filter.type === "async-select" ||
      filter.type === "search" ||
      value in filter.options
    ) {
      clean[filter.key] = value;
    }
  }

  return clean;
}

export const toFilterOptions = (items: CatalogItem[]): AdminFilterOptions =>
  Object.fromEntries(items.map((item) => [item.id, item.name]));
