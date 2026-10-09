import propertiesApi from "@/api/propertiesApi";
import { PROPERTIES_ENDPOINTS } from "@/constants/propertiesEndpoints";
import type { PublicUserPropertiesResponse } from "@/types/users/profile";

export async function fetchUserListings(account_id: string, offset: number) {
  const { data } = await propertiesApi.get<PublicUserPropertiesResponse>(
    PROPERTIES_ENDPOINTS.byUser(account_id),
    {
      params: { offset },
      paramsSerializer: { indexes: null },
    }
  );
  return { items: data.items, hasMore: data.has_more };
}
