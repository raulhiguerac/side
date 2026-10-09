import * as propertiesApi from "@/api/properties";

export async function fetchUserListings(account_id: string, offset: number) {
  const data = await propertiesApi.getUserListings(account_id, offset);
  return { items: data.items, hasMore: data.has_more };
}
