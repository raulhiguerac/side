import * as adminCatalogApi from "@/api/admin/catalog";
import { useAdminPage } from "@/composables/admin/useAdminPage";
import { PAGE_SIZE } from "@/constants/pagination";
import type { LocalityAdminPage } from "@/types/admin/catalog";
import { pickFilters } from "@/utils/adminFilters";

const FILTER_KEYS = ["country_id", "admin_division_id", "is_active"] as const;

export function useAdminLocalities() {
  return useAdminPage<LocalityAdminPage>({
    fetch: (page, filters) =>
      adminCatalogApi.getLocalities({
        ...page,
        ...pickFilters(filters, FILTER_KEYS),
      }),
    pageSize: PAGE_SIZE.ADMIN_LOCALITIES,
    errorMessage: "No se pudieron cargar las localidades",
  });
}
