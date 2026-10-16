import type { Component } from "vue";

export type ButtonSize = "sm" | "md" | "lg" | "xl";

export type ButtonVariant =
  | "primary"
  | "secondary"
  | "ghost"
  | "danger"
  | "danger-soft"
  | "link";

export type IconButtonSize = "xs" | "sm" | "md" | "lg";

/** `surface`: círculo blanco sobre fotos; `plain`: sin fondo hasta el hover. */
export type IconButtonVariant = "surface" | "plain";

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

// Una línea de la lista ✓/✕ de `FileUploadField`.
export interface FileRequirement {
  text: string;
  accepted: boolean;
}
