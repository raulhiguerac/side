export function formatMoney(value: number | null): string {
  if (!value) return "";
  return value.toLocaleString("es-CO");
}

export function parseMoney(raw: string): number | null {
  const n = parseInt(raw.replace(/\D/g, ""), 10);
  return isNaN(n) ? null : n;
}
