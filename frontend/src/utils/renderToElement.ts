import { h, render, type Component } from "vue";

// Para APIs que piden HTML fuera de Vue (iconos y popups de Leaflet).
export function renderToElement(
  component: Component,
  props: Record<string, unknown> = {}
): HTMLElement {
  const el = document.createElement("div");
  render(h(component, props), el);
  return el;
}
