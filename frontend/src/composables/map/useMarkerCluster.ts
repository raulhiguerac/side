import * as L from "leaflet";
import "leaflet.markercluster/dist/MarkerCluster.css";
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { MarkerClusterGroup } = require("leaflet.markercluster");
import type {} from "leaflet.markercluster"; // tipos de L.MarkerClusterGroup
import type { MarkerData } from "@/types/maps/base";
import type { MarkerClusterHandlers } from "@/types/maps/cluster";
import { clusterIcon, markerIcon } from "@/utils/markerIcon";

interface Entry {
  data: MarkerData;
  marker: L.Marker;
}

function samePlace(a: MarkerData, b: MarkerData): boolean {
  return a.lat === b.lat && a.lon === b.lon && a.imageType === b.imageType;
}

export function useMarkerCluster(handlers: MarkerClusterHandlers = {}) {
  let map: L.Map | null = null;
  const group: L.MarkerClusterGroup = new MarkerClusterGroup({
    maxClusterRadius: 50,
    chunkedLoading: true,
    showCoverageOnHover: false,
    iconCreateFunction: (cluster: L.MarkerCluster) =>
      clusterIcon(cluster.getChildCount()),
  });
  const entries = new Map<string, Entry>();
  let highlightedId: string | null = null;
  let highlightedCluster: HTMLElement | null = null;

  function createMarker(data: MarkerData): L.Marker {
    const marker = L.marker([data.lat, data.lon], {
      icon: markerIcon(data.imageType, data.id === highlightedId),
    });
    const popup = handlers.popup?.(data);
    if (popup) marker.bindPopup(popup);
    if (handlers.onClick) marker.on("click", () => handlers.onClick?.(data));
    if (handlers.onHover) {
      marker.on("mouseover", () => handlers.onHover?.(data.id));
      marker.on("mouseout", () => handlers.onHover?.(null));
    }
    return marker;
  }

  // Por diferencias: solo entra y sale lo que cambió, no se rearma el grupo.
  function sync(markers: MarkerData[]) {
    const next = new Map(markers.map((m) => [m.id, m]));
    const toRemove: L.Marker[] = [];
    const toAdd: L.Marker[] = [];

    for (const [id, entry] of entries) {
      const data = next.get(id);
      if (data && samePlace(data, entry.data)) continue;
      toRemove.push(entry.marker);
      entries.delete(id);
    }
    for (const data of markers) {
      if (entries.has(data.id)) continue;
      const marker = createMarker(data);
      entries.set(data.id, { data, marker });
      toAdd.push(marker);
    }

    if (toRemove.length) group.removeLayers(toRemove);
    if (toAdd.length) group.addLayers(toAdd);
    refreshClusterHighlight();
  }

  function refreshClusterHighlight() {
    highlightedCluster?.classList.remove("is-highlighted");
    highlightedCluster = null;
    const entry = highlightedId ? entries.get(highlightedId) : undefined;
    if (!entry) return;
    // Si el marcador está dentro de una burbuja, se resalta la burbuja.
    const parent = group.getVisibleParent(entry.marker);
    if (parent && parent !== entry.marker) {
      highlightedCluster = parent.getElement() ?? null;
      highlightedCluster?.classList.add("is-highlighted");
    }
  }

  function highlight(id: string | null) {
    const previous = highlightedId ? entries.get(highlightedId) : undefined;
    previous?.marker.setIcon(markerIcon(previous.data.imageType, false));
    highlightedId = id;
    const current = id ? entries.get(id) : undefined;
    current?.marker.setIcon(markerIcon(current.data.imageType, true));
    refreshClusterHighlight();
  }

  function attach(instance: L.Map) {
    map = instance;
    map.addLayer(group);
    group.on("animationend", refreshClusterHighlight);
    map.on("zoomend", refreshClusterHighlight);
  }

  function detach() {
    if (!map) return;
    map.off("zoomend", refreshClusterHighlight);
    map.removeLayer(group);
    map = null;
  }

  return { attach, detach, sync, highlight };
}
