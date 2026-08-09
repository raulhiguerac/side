export function formatMoney(value: number | null): string {
  if (!value) return "";
  return value.toLocaleString("es-CO");
}

export function parseMoney(raw: string): number | null {
  const n = parseInt(raw.replace(/\D/g, ""), 10);
  return isNaN(n) ? null : n;
}

/** Como `formatMoney` pero con símbolo; acepta string porque los `Decimal` del backend llegan así. */
export function formatCurrency(
  value: number | string | null,
  currency = "COP"
): string {
  if (value === null || value === "") return "";
  const amount = typeof value === "string" ? Number(value) : value;
  if (Number.isNaN(amount)) return "";

  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(amount);
}
