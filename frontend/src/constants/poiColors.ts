import type { MarkerImageType } from "@/types/maps/base";

export const POI_COLORS: Partial<Record<MarkerImageType, string>> = {
  food: "#f97316",
  education: "#3b82f6",
  health: "#ef4444",
  transport: "#8b5cf6",
  commerce: "#eab308",
  poi: "#6b7280",
};

export const POI_BUCKET_LABELS: Partial<Record<MarkerImageType, string>> = {
  food: "Comida",
  education: "Educación",
  health: "Salud",
  transport: "Transporte",
  commerce: "Comercio",
  poi: "Otros",
};

export const ISOCHRONE_COLORS: Record<number, string> = {
  15: "#6366f1",
  10: "#22c55e",
  5: "#ef4444",
};
