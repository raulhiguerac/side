import type { FieldSize } from "@/types/shared/ui";

// Un solo look para input, select y textarea; el alto lo pone cada uno.
export const FIELD_BASE =
  "w-full rounded-xl border bg-white text-sm text-brand-text placeholder:text-brand-placeholder transition-colors focus:border-brand-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary/30 disabled:cursor-not-allowed disabled:opacity-50";

export const FIELD_SIZE: Record<FieldSize, string> = {
  md: "h-10 px-3",
  lg: "h-12 px-4",
};

export const fieldBorder = (invalid: boolean) =>
  invalid ? "border-brand-danger" : "border-brand-border";
