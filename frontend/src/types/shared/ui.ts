export type ButtonSize = "sm" | "md" | "lg";

export interface TabOption<V extends string = string> {
  label: string;
  value: V;
}

export type ColumnAlign = "left" | "right";

export interface ColumnMeta {
  align?: ColumnAlign;
}

export type MessageVariant = "error" | "success";
