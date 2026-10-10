import type { MarkerData } from "@/types/maps/base";

export interface MarkerClusterHandlers {
  onClick?: (marker: MarkerData) => void;
  onHover?: (id: string | null) => void;
  popup?: (marker: MarkerData) => HTMLElement | undefined;
}
