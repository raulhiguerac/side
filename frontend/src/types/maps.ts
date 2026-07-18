// Evoluciona con el tiempo (más categorías de POI, etc.)
export type MarkerImageType =
  // el inmueble que se está avaluando — marker propio, diferenciado
  | "subject"
  // propiedades comparables
  | "house"
  | "apartment"
  // POIs por categoría
  | "food"
  | "education"
  | "health"
  | "transport"
  | "commerce"
  | "poi";

export interface MarkerData {
  id: string;
  lat: number;
  lon: number;
  imageType: MarkerImageType;
  label?: string;
  categoryLabel?: string;
  address?: string;
  phone?: string;
  website?: string;
}
