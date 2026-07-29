const shortDateFormatter = new Intl.DateTimeFormat("es-CO", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

/**
 * `12 jul 2026`. El formateador se crea una sola vez a nivel de módulo:
 * construir un `Intl.DateTimeFormat` por celda es de lo más caro que puede
 * hacer una tabla con cientos de filas.
 */
export function formatShortDate(value: string | Date | null): string {
  if (!value) return "";
  const date = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return "";
  return shortDateFormatter.format(date);
}
