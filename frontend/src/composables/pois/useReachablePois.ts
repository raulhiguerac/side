import axios from "axios";
import { ref, computed } from "vue";
import type { Component } from "vue";
import { API } from "@/config";
import { Footprints, Bike, Car } from "@lucide/vue";
import type {
  RangeGroup,
  ReachablePoisResult,
  OrsProfile,
  ProfileOption,
  ReachablePoiItem,
} from "@/types/pois";
import { CATEGORY_META, CATEGORY_PRIORITY } from "@/types/pois";

interface CategoryGroup {
  label: string;
  icon: Component;
  pois: ReachablePoiItem[];
}

export interface RangeWithGroups extends RangeGroup {
  groups: CategoryGroup[];
}

export const ISOCHRONE_COLORS: Record<number, string> = {
  15: "#6366f1",
  10: "#22c55e",
  5: "#ef4444",
};

const DOT_BY_SECONDS: Record<number, string> = {
  300: "bg-red-500",
  600: "bg-green-500",
  900: "bg-indigo-500",
};

async function fetchPois(
  lat: number,
  lon: number,
  propertyId: string
): Promise<ReachablePoisResult[]> {
  try {
    const { data } = await axios.post(
      `${API.CATALOG_BASE_URL}/v1/geo-resolution/reachable-pois`,
      {
        lat: lat,
        lon: lon,
        range_seconds: [300, 600, 900],
        profile: ["foot-walking", "cycling-regular", "driving-car"],
        property_id: propertyId,
      }
    );
    return data as Array<ReachablePoisResult>;
  } catch (error) {
    console.error("Error al obtener pois:", error);
    return [];
  }
}

function groupByCategory(pois: ReachablePoiItem[]): CategoryGroup[] {
  const grouped: Record<string, CategoryGroup> = {};
  for (const poi of pois) {
    const meta = CATEGORY_META[poi.category ?? ""];
    if (!meta) continue;
    if (poi.name.toLowerCase() === (poi.category ?? "").toLowerCase()) continue;
    const key = meta.label;
    if (!grouped[key])
      grouped[key] = { label: meta.label, icon: meta.icon, pois: [] };
    if (grouped[key].pois.length < 2) grouped[key].pois.push(poi);
  }
  return Object.values(grouped).sort(
    (a, b) =>
      (CATEGORY_PRIORITY[a.pois[0]?.category ?? ""] ?? 99) -
      (CATEGORY_PRIORITY[b.pois[0]?.category ?? ""] ?? 99)
  );
}

export function useReachablePois(profile: OrsProfile) {
  const activeProfile = ref<OrsProfile>(profile);
  const ranges = ref<RangeGroup[]>([]);
  const loading = ref<boolean>(false);

  const profiles: ProfileOption[] = [
    {
      key: "foot-walking",
      label: "A pie",
      icon: Footprints,
      description: "Distancia caminando desde la propiedad",
    },
    {
      key: "cycling-regular",
      label: "En bici",
      icon: Bike,
      description: "Distancia en bicicleta desde la propiedad",
    },
    {
      key: "driving-car",
      label: "En carro",
      icon: Car,
      description: "Distancia en carro desde la propiedad",
    },
  ];

  async function loadPois(lat: number, lon: number, propertyId: string) {
    try {
      loading.value = true;
      ranges.value = [];
      const pois = await fetchPois(lat, lon, propertyId);
      for (const result of pois) {
        if (result.range === null) continue;
        ranges.value.push({
          profile: result.profile,
          minutes: result.range / 60,
          seconds: result.range,
          dot: DOT_BY_SECONDS[result.range] ?? "bg-green-300",
          count: result.pois.length,
          pois: result.pois,
          isochrone: result.isochrone,
        });
      }
    } finally {
      loading.value = false;
    }
  }

  const groupedByRange = computed<RangeWithGroups[]>(() =>
    ranges.value
      .filter((r) => r.profile === activeProfile.value)
      .map((range) => ({
        ...range,
        groups: groupByCategory(range.pois).slice(0, 8),
      }))
  );

  return { activeProfile, profiles, ranges, groupedByRange, loading, loadPois };
}
