import * as adminCatalogApi from "@/api/admin/catalog";
import { useAdminPage } from "@/composables/admin/useAdminPage";
import { PAGE_SIZE } from "@/constants/pagination";
import type { CountryAdminPage } from "@/types/admin/catalog";
import { pickFilters } from "@/utils/adminFilters";

const FILTER_KEYS = ["is_active", "is_supported"] as const;

export function useAdminCountries() {
  return useAdminPage<CountryAdminPage>({
    fetch: (page, filters) =>
      adminCatalogApi.getAdminCountries({
        ...page,
        ...pickFilters(filters, FILTER_KEYS),
      }),
    pageSize: PAGE_SIZE.ADMIN_COUNTRIES,
    errorMessage: "No se pudieron cargar los países",
  });
}
