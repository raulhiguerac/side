const shortDateFormatter = new Intl.DateTimeFormat("es-CO", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

/** `12 jul 2026`. El formateador se crea una vez por módulo: uno por celda es carísimo en tablas grandes. */
export function formatShortDate(value: string | Date | null): string {
  if (!value) return "";
  const date = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return "";
  return shortDateFormatter.format(date);
}
