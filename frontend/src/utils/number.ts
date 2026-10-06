import { LOCALE } from "@/config";

const numberFormatter = new Intl.NumberFormat(LOCALE);
const kmFormatter = new Intl.NumberFormat(LOCALE, { maximumFractionDigits: 2 });

export const formatNumber = (value: number) => numberFormatter.format(value);

// m² bajo 1 km², km² desde ahí.
export function formatArea(m2: number | null): string {
  if (m2 == null) return "—";
  if (m2 < 1_000_000) return `${formatNumber(Math.round(m2))} m²`;
  return `${kmFormatter.format(m2 / 1_000_000)} km²`;
}
