import type { Component } from "vue";

export type ButtonSize = "sm" | "md" | "lg";

export interface TabOption<V extends string = string> {
  label: string;
  value: V;
}

export type ColumnAlign = "left" | "right";

export type MessageVariant = "error" | "success";

// Opción de un selector de tarjetas con icono.
export interface ChoiceOption<V extends string> {
  value: V;
  label: string;
  desc?: string;
  icon: Component;
}
