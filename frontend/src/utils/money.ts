export function formatMoney(value: number | null): string {
  if (!value) return "";
  return value.toLocaleString("es-CO");
}

export function parseMoney(raw: string): number | null {
  const n = parseInt(raw.replace(/\D/g, ""), 10);
  return isNaN(n) ? null : n;
}

/**
 * Igual que `formatMoney` pero con símbolo de moneda. Existe porque el mismo
 * `Intl.NumberFormat` está repetido en `usePropertyDetail` (precio y admin fee)
 * y hay variantes a mano en `AvmResult` y `PropertyCard` — este es el lugar
 * donde deberían converger.
 *
 * Acepta string porque los `Decimal` del backend se serializan así.
 */
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
