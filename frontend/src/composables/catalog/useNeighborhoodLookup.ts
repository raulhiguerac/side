import { getNeighborhoodsByLocalities } from "@/composables/catalog/useLocation";

export async function buildNeighborhoodMap(
  localityIds: string[]
): Promise<Record<string, string>> {
  const result = await getNeighborhoodsByLocalities(localityIds);
  const neighborhoods = Object.values(result).flat();
  const names = neighborhoods.reduce(
    (acc, n) => ({ ...acc, [n.id]: n.name }),
    {} as Record<string, string>
  );

  return names;
}
