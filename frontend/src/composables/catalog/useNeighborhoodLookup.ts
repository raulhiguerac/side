import { getNeighborhoodsByLocalities } from "@/composables/catalog/useLocation";

export async function buildNeighborhoodMap(
  localityIds: string[]
): Promise<Record<string, string>> {
  const result = await getNeighborhoodsByLocalities(localityIds);
  const neighborhoods = Object.values(result).flat();
  return Object.fromEntries(neighborhoods.map((n) => [n.id, n.name]));
}
