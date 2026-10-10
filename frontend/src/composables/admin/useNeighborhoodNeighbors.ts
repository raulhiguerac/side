import { ref } from "vue";
import * as adminCatalogApi from "@/api/admin/catalog";
import type { NeighborhoodGeometryItem } from "@/types/admin/catalog";
import type { Bbox } from "@/types/maps/base";
import { logger } from "@/utils/logger";

/** Los vecinos son contexto: si fallan (p. ej. bbox mayor al tope del backend) el mapa queda sin ellos. */
export function useNeighborhoodNeighbors() {
  const neighbors = ref<NeighborhoodGeometryItem[]>([]);
  let latestRequest = 0;

  async function load(neighborhoodId: string, bbox: Bbox) {
    const request = ++latestRequest;
    try {
      const data = await adminCatalogApi.getNeighborhoodGeometries(
        neighborhoodId,
        bbox
      );
      if (request === latestRequest) neighbors.value = data;
    } catch (e) {
      if (request === latestRequest) neighbors.value = [];
      logger.error("admin neighborhood neighbors failed", e);
    }
  }

  function clear() {
    latestRequest++;
    neighbors.value = [];
  }

  return { neighbors, load, clear };
}
