import * as L from "leaflet";
import { BRAND_COLORS } from "@/constants/brandColors";
import { markerIconMap } from "@/constants/markerIcons";
import { POI_COLORS } from "@/constants/poiColors";
import type { MarkerImageType } from "@/types/maps/base";
import { renderToElement } from "@/utils/renderToElement";

const PIN_TYPES: MarkerImageType[] = ["house", "subject"];
const PROPERTY_TYPES: MarkerImageType[] = ["house", "subject", "apartment"];

function iconSize(type: MarkerImageType, highlighted: boolean): number {
  if (PROPERTY_TYPES.includes(type)) return highlighted ? 48 : 24;
  return highlighted ? 32 : 20;
}

// Un render de Vue por tipo y estado; el resto de marcadores reusa el string.
const htmlCache = new Map<string, string>();

function iconHtml(type: MarkerImageType, highlighted: boolean): string {
  const key = `${type}:${highlighted}`;
  const cached = htmlCache.get(key);
  if (cached) return cached;

  const Icon = markerIconMap[type];
  const fill = highlighted ? BRAND_COLORS.primary : BRAND_COLORS.navy;
  let html: string;

  const size = iconSize(type, highlighted);
  if (PIN_TYPES.includes(type)) {
    html = renderToElement(Icon, {
      size,
      color: "white",
      fill,
    }).innerHTML;
  } else {
    const bg = PROPERTY_TYPES.includes(type)
      ? fill
      : POI_COLORS[type] ?? BRAND_COLORS.muted;
    const svg = renderToElement(Icon, {
      size: Math.round(size * 0.58),
      color: "white",
    }).innerHTML;
    html = `<div style="width:${size}px;height:${size}px;background:${bg};border-radius:9999px;display:flex;align-items:center;justify-content:center;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.4)">${svg}</div>`;
  }

  htmlCache.set(key, html);
  return html;
}

export function markerIcon(
  type: MarkerImageType,
  highlighted = false
): L.DivIcon {
  const isPin = PIN_TYPES.includes(type);
  const size = iconSize(type, highlighted);
  return L.divIcon({
    html: iconHtml(type, highlighted),
    className: "",
    iconSize: [size, size],
    // Los pines apuntan con la punta; los círculos, con el centro.
    iconAnchor: isPin ? [size / 2, size] : [size / 2, size / 2],
  });
}

export function clusterIcon(count: number): L.DivIcon {
  const size = count < 10 ? 32 : count < 100 ? 40 : 48;
  return L.divIcon({
    html: `<div style="width:${size}px;height:${size}px;background:${BRAND_COLORS.navy};color:white;border-radius:9999px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:600;border:3px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.4)">${count}</div>`,
    className: "map-cluster",
    iconSize: [size, size],
  });
}
