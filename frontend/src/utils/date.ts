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

const shortDateTimeFormatter = new Intl.DateTimeFormat("es-CO", {
  day: "2-digit",
  month: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
});

/** `24/08, 14:32`. Sin año: en una tabla de corridas lo que importa es cuál fue antes. */
export function formatShortDateTime(value: string | Date | null): string {
  if (!value) return "";
  const date = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return "";
  return shortDateTimeFormatter.format(date);
}
