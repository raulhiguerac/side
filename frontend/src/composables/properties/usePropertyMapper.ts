import { ref, computed, watch } from "vue";
import type { Ref } from "vue";
import type { PropertyCard as FeedCard } from "@/types/feed";
import type { Property } from "@/components/properties/PropertyCard.vue";
import { buildNeighborhoodMap } from "@/composables/catalog/useNeighborhoodLookup";

export function usePropertyMapper(items: Ref<FeedCard[]>) {
  const neighborhoodLookup = ref<Record<string, string>>({});

  watch(items, async (newItems) => {
    const cityIds = [
      ...new Set(
        newItems.map((p) => p.location?.city_id).filter(Boolean) as string[]
      ),
    ];
    if (cityIds.length) {
      neighborhoodLookup.value = await buildNeighborhoodMap(cityIds);
    }
  });

  function toCard(p: FeedCard): Property {
    const typeLabel = p.property_type === "house" ? "Casa" : "Apartamento";
    const listingLabel = p.listing_type === "sale" ? "en venta" : "en arriendo";
    return {
      id: p.id,
      title: `${typeLabel} ${listingLabel}`,
      price: Number(p.price),
      location:
        neighborhoodLookup.value[p.location?.neighborhood_id ?? ""] ?? "",
      image: p.images.find((i) => i.is_cover)?.url ?? p.images[0]?.url,
      type: p.listing_type,
      bedrooms: p.bedrooms,
      bathrooms: Number(p.bathrooms),
      area: Number(p.area_m2),
    };
  }

  const cards = computed(() => items.value.map(toCard));

  return { cards };
}
