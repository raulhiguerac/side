import * as adminCatalogApi from "@/api/admin/catalog";
import { useAdminPage } from "@/composables/admin/useAdminPage";
import { PAGE_SIZE } from "@/constants/pagination";
import type { DivisionAdminPage } from "@/types/admin/catalog";
import { pickFilters } from "@/utils/adminFilters";

const FILTER_KEYS = ["country_id", "is_active"] as const;

export function useAdminDivisions() {
  return useAdminPage<DivisionAdminPage>({
    fetch: (page, filters) =>
      adminCatalogApi.getAdminDivisions({
        ...page,
        ...pickFilters(filters, FILTER_KEYS),
      }),
    pageSize: PAGE_SIZE.ADMIN_DIVISIONS,
    errorMessage: "No se pudieron cargar las divisiones",
  });
}
