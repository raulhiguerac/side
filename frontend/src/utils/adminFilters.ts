import type { LocationQuery } from "vue-router";
import type { CatalogItem } from "@/types/catalog/base";
import type {
  AdminFilterDefinition,
  AdminFilterOptions,
} from "@/types/admin/filters";

// Solo keys definidas y valores del enum: `?status=banana` sería un 422.
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

// Lo que el endpoint acepta de la URL; el resto (p. ej. el país de la cascada) no viaja.
export function pickFilters<K extends string>(
  source: Record<string, string>,
  keys: readonly K[]
): Partial<Record<K, string>> {
  const picked: Partial<Record<K, string>> = {};
  for (const key of keys) {
    if (source[key]) picked[key] = source[key];
  }
  return picked;
}
