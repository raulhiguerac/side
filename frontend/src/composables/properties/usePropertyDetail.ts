import { computed } from "vue";
import type { Ref } from "vue";
import type { PropertyDetail } from "@/types/properties";

export function usePropertyDetail(property: Ref<PropertyDetail | null>) {
  const title = computed(() => {
    if (!property.value) return "";
    const type = property.value.property_type === "apartment" ? "Apartamento" : "Casa";
    const mode = property.value.listing_type === "sale" ? "en venta" : "en arriendo";
    return `${type} ${mode}`;
  });

  const formattedPrice = computed(() => {
    if (!property.value) return "";
    return new Intl.NumberFormat("es-CO", {
      style: "currency",
      currency: property.value.currency,
      maximumFractionDigits: 0,
    }).format(property.value.price);
  });

  const formattedAdminFee = computed(() => {
    if (!property.value?.admin_fee) return "";
    return new Intl.NumberFormat("es-CO", {
      style: "currency",
      currency: property.value.currency,
      maximumFractionDigits: 0,
    }).format(property.value.admin_fee);
  });

  const stats = computed(() => {
    const p = property.value;
    if (!p) return [];
    return [
      { label: "Habitaciones", value: p.bedrooms },
      { label: "Baños",        value: p.bathrooms },
      { label: "Área",         value: `${p.area_m2} m²` },
      { label: "Parqueaderos", value: p.parking_spots },
      ...(p.floor_number != null ? [{ label: "Piso",    value: p.floor_number }] : []),
      ...(p.stratum      != null ? [{ label: "Estrato", value: p.stratum }]      : []),
    ];
  });

  const details = computed(() => {
    const p = property.value;
    if (!p) return [];
    const conditionMap: Record<string, string> = { new: "Nuevo", used: "Usado", remodeled: "Remodelado" };
    return [
      { label: "Condición",      value: conditionMap[p.condition] ?? p.condition },
      { label: "Año construido", value: p.year_built ?? "—" },
      ...(p.total_floors != null ? [{ label: "Total pisos", value: p.total_floors }] : []),
    ];
  });

  const statusLabel = computed(() => {
    const map: Record<string, string> = {
      active: "Activo", draft: "Borrador", inactive: "Inactivo", sold: "Vendido", rented: "Arrendado",
    };
    return map[property.value?.status ?? ""] ?? "";
  });

  const statusStyle = computed(() => {
    const map: Record<string, string> = {
      active:   "bg-green-100 text-green-700",
      draft:    "bg-gray-100 text-gray-500",
      inactive: "bg-yellow-100 text-yellow-700",
      sold:     "bg-blue-100 text-blue-700",
      rented:   "bg-purple-100 text-purple-700",
    };
    return map[property.value?.status ?? ""] ?? "";
  });

  const verificationLabel = computed(() => {
    const map: Record<string, string> = {
      verified:   "Verificado",
      unverified: "Sin verificar",
      pending:    "En revisión",
      rejected:   "Rechazado",
    };
    return map[property.value?.verification_status ?? ""] ?? "";
  });

  const verificationStyle = computed(() => {
    const map: Record<string, string> = {
      verified:   "bg-brand-primary-light text-green-700",
      unverified: "bg-gray-100 text-gray-500",
      pending:    "bg-yellow-100 text-yellow-700",
      rejected:   "bg-red-100 text-red-600",
    };
    return map[property.value?.verification_status ?? ""] ?? "";
  });

  const mapCenter = computed((): [number, number] | null => {
    const loc = property.value?.location;
    return loc ? [loc.latitude, loc.longitude] : null;
  });

  const gridImages = computed(() => property.value?.images.slice(0, 5) ?? []);

  return {
    title,
    formattedPrice,
    formattedAdminFee,
    stats,
    details,
    statusLabel,
    statusStyle,
    verificationLabel,
    verificationStyle,
    mapCenter,
    gridImages,
  };
}
