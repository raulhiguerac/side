import type { Component } from "vue";

export type AdminActionVariant = "default" | "primary" | "danger";

/** Un botón de `AdminActionBar`; `key` es lo que emite al hacer click. */
export interface AdminAction<K extends string = string> {
  key: K;
  icon: Component;
  label: string;
  variant?: AdminActionVariant;
}
