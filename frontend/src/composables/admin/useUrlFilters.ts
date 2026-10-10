import { computed, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import type { AdminFilterDefinition } from "@/types/admin/filters";
import { sanitizeFilterQuery } from "@/utils/adminFilters";

// La URL manda: el filtro se comparte y, con push, el back lo deshace.
export function useUrlFilters<T extends object = Record<string, string>>(
  filters: readonly AdminFilterDefinition[],
  onChange: (values: T) => void
) {
  const route = useRoute();
  const router = useRouter();

  const urlFilters = computed(() => sanitizeFilterQuery(route.query, filters));

  function pushFilters(values: Record<string, string>) {
    router.push({ query: values });
  }

  // Único cast: sanitizeFilterQuery ya validó cada valor contra su enum.
  watch(urlFilters, (values) => onChange(values as T), { immediate: true });

  return { urlFilters, pushFilters };
}
