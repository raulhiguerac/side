import { computed } from "vue";
import * as adminCatalogApi from "@/api/admin/catalog";
import { useAdminPage } from "@/composables/admin/useAdminPage";
import { PAGE_SIZE } from "@/constants/pagination";
import type { NeighborhoodAdminPage } from "@/types/admin/catalog";
import { pickFilters } from "@/utils/adminFilters";

// `country_id` solo acota el select de localidad: no se manda.
const FILTER_KEYS = [
  "locality_id",
  "is_active",
  "has_geometry",
  "search_term",
] as const;

export function useAdminNeighborhoods() {
  const list = useAdminPage<NeighborhoodAdminPage>({
    fetch: (page, filters) =>
      adminCatalogApi.getNeighborhoods({
        ...page,
        ...pickFilters(filters, FILTER_KEYS),
      }),
    pageSize: PAGE_SIZE.ADMIN_NEIGHBORHOODS,
    errorMessage: "No se pudieron cargar los barrios",
  });

  return {
    ...list,
    coverage: computed(() => list.page.value?.coverage ?? null),
  };
}
