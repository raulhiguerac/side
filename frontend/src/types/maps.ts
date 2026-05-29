// Evoluciona con el tiempo (más categorías de POI, etc.)
export type MarkerImageType =
  // el inmueble que se está avaluando — marker propio, diferenciado
  | "subject"
  // propiedades comparables
  | "house"
  | "apartment"
  // POIs por categoría
  | "food"
  | "education";

export interface MarkerData {
  id: string;
  lat: number;
  lon: number;
  imageType: MarkerImageType;
}
