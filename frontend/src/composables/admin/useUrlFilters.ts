import { computed, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import type { AdminFilterDefinition } from "@/types/admin/filters";
import { sanitizeFilterQuery } from "@/utils/adminFilters";

// La URL manda: el filtro se comparte y, con push, el back lo deshace.
export function useUrlFilters(
  filters: readonly AdminFilterDefinition[],
  onChange: (values: Record<string, string>) => void
) {
  const route = useRoute();
  const router = useRouter();

  const urlFilters = computed(() => sanitizeFilterQuery(route.query, filters));

  function pushFilters(values: Record<string, string>) {
    router.push({ query: values });
  }

  watch(urlFilters, onChange, { immediate: true });

  return { urlFilters, pushFilters };
}
