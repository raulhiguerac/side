import { ref } from "vue";
import propertiesApi from "@/api/propertiesApi";
import type { PropertyCard } from "@/types/feed";

interface PublicUserPropertiesResponse {
  items: PropertyCard[];
  has_more: boolean;
}

export function useProfileListings() {
  const all_listings: PropertyCard[] = [];
  const listings = ref<PropertyCard[]>([]);
  const hasMore = ref(false);

  async function fetchUserListings(account_id: string, offset: number) {
    try {
      const { data } = await propertiesApi.get<PublicUserPropertiesResponse>(
        `/v1/properties/users/${account_id}`,
        {
          params: { offset },
          paramsSerializer: { indexes: null },
        }
      );
      all_listings.push(...data.items);
      listings.value = data.items;
      hasMore.value = data.has_more;
    } catch (error) {
      console.error("Error al obtener listings:", error);
    }
  }

  function previousListings(page: number) {
    if (page < 2) return;
    listings.value = all_listings.slice((page - 2) * 20, (page - 1) * 20);
  }

  return { listings, hasMore, fetchUserListings, previousListings };
}
