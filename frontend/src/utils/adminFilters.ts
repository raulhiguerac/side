import type { LocationQuery } from "vue-router";
import type { AdminFilterDefinition } from "@/types/admin";

/** Deja solo las keys definidas con un valor del enum: la query la escribe
 * cualquiera, y `?status=banana` es un 422 del backend. */
export function sanitizeFilterQuery(
  query: LocationQuery,
  filters: readonly AdminFilterDefinition[]
): Record<string, string> {
  const clean: Record<string, string> = {};

  for (const filter of filters) {
    // Una key repetida llega como array: ahí no hay un valor único que aplicar.
    const value = query[filter.key];
    if (typeof value === "string" && value in filter.options) {
      clean[filter.key] = value;
    }
  }

  return clean;
}
