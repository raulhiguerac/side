import type { PropertyCard } from "@/types/feed/cards";
import type { BboxPayload } from "@/types/feed/search";

// Distancia al cuadrado con la longitud escalada por la latitud: basta para ordenar.
function distanceSq(card: PropertyCard, lat: number, lon: number): number {
  const loc = card.location;
  if (loc?.latitude == null || loc.longitude == null) return Infinity;
  const dLat = loc.latitude - lat;
  const dLon = (loc.longitude - lon) * Math.cos((lat * Math.PI) / 180);
  return dLat * dLat + dLon * dLon;
}

// Promocionadas primero, luego de más cerca a más lejos del centro del bbox.
export function sortForMap(
  cards: PropertyCard[],
  bbox: BboxPayload
): PropertyCard[] {
  const lat = (bbox.min_lat + bbox.max_lat) / 2;
  const lon = (bbox.min_lon + bbox.max_lon) / 2;
  const distance = new Map(cards.map((c) => [c.id, distanceSq(c, lat, lon)]));
  const byDistance = (a: PropertyCard, b: PropertyCard) => {
    const da = distance.get(a.id) ?? Infinity;
    const db = distance.get(b.id) ?? Infinity;
    return da === db ? 0 : da - db;
  };
  return [...cards].sort(
    (a, b) =>
      Number(b.is_promoted) - Number(a.is_promoted) ||
      byDistance(a, b) ||
      a.id.localeCompare(b.id)
  );
}
