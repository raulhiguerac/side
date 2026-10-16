import { Ref, computed } from "vue";
import type { PropertyDetail } from "@/types/properties/detail";
import { formatCurrency } from "@/utils/money";
import { propertyTitle } from "@/utils/property";

export function usePropertyDetail(property: Ref<PropertyDetail | null>) {
  const title = computed(() =>
    property.value
      ? propertyTitle(property.value.property_type, property.value.listing_type)
      : ""
  );

  const formattedPrice = computed(() =>
    property.value
      ? formatCurrency(property.value.price, property.value.currency)
      : ""
  );

  const formattedAdminFee = computed(() =>
    property.value?.admin_fee
      ? formatCurrency(property.value.admin_fee, property.value.currency)
      : ""
  );

  const stats = computed(() => {
    const p = property.value;
    if (!p) return [];
    return [
      { label: "Habitaciones", value: p.bedrooms },
      { label: "Baños", value: p.bathrooms },
      { label: "Área", value: `${p.area_m2} m²` },
      { label: "Parqueaderos", value: p.parking_spots },
      ...(p.floor_number != null
        ? [{ label: "Piso", value: p.floor_number }]
        : []),
      ...(p.stratum != null ? [{ label: "Estrato", value: p.stratum }] : []),
    ];
  });

  const details = computed(() => {
    const p = property.value;
    if (!p) return [];
    const conditionMap: Record<string, string> = {
      new: "Nuevo",
      used: "Usado",
      remodeled: "Remodelado",
    };
    return [
      { label: "Condición", value: conditionMap[p.condition] ?? p.condition },
      { label: "Año construido", value: p.year_built ?? "—" },
      ...(p.total_floors != null
        ? [{ label: "Total pisos", value: p.total_floors }]
        : []),
    ];
  });

  const statusLabel = computed(() => {
    const map: Record<string, string> = {
      active: "Activo",
      draft: "Borrador",
      inactive: "Inactivo",
      sold: "Vendido",
      rented: "Arrendado",
    };
    return map[property.value?.status ?? ""] ?? "";
  });

  const statusStyle = computed(() => {
    const map: Record<string, string> = {
      active: "bg-brand-success-light text-brand-success",
      draft: "bg-gray-100 text-gray-500",
      inactive: "bg-brand-warning-light text-brand-warning",
      sold: "bg-blue-100 text-blue-700",
      rented: "bg-purple-100 text-purple-700",
    };
    return map[property.value?.status ?? ""] ?? "";
  });

  const verificationLabel = computed(() => {
    const map: Record<string, string> = {
      verified: "Verificado",
      unverified: "Sin verificar",
      pending: "En revisión",
      rejected: "Rechazado",
    };
    return map[property.value?.verification_status ?? ""] ?? "";
  });

  const verificationStyle = computed(() => {
    const map: Record<string, string> = {
      verified: "bg-brand-primary-light text-brand-success",
      unverified: "bg-gray-100 text-gray-500",
      pending: "bg-brand-warning-light text-brand-warning",
      rejected: "bg-brand-danger-light text-brand-danger",
    };
    return map[property.value?.verification_status ?? ""] ?? "";
  });

  const gridImages = computed(() => property.value?.images.slice(0, 5) ?? []);

  const hasAdminFee = computed(() => !!property.value?.admin_fee);

  const description = computed(() => property.value?.description ?? null);

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
    gridImages,
    hasAdminFee,
    description,
  };
}
