import {
  loadCountryOptions,
  loadDivisionOptions,
  loadLocalityOptions,
} from "@/api/admin/catalog";
import type {
  AdminAsyncSelectFilter,
  AdminFilterDefinition,
  AdminStaticSelectFilter,
} from "@/types/admin/filters";

// Piezas compartidas: las usan las barras de filtros y las cascadas de los modales.
// País y localidad usan los GET públicos (solo activos) hasta tener los admin.
export const COUNTRY_SELECT: AdminAsyncSelectFilter = {
  type: "async-select",
  key: "country_id",
  label: "País",
  allLabel: "Todos",
  loadOptions: loadCountryOptions,
};

export const DIVISION_SELECT: AdminAsyncSelectFilter = {
  type: "async-select",
  key: "admin_division_id",
  label: "División",
  dependsOn: "country_id",
  loadOptions: loadDivisionOptions,
};

export const LOCALITY_SELECT: AdminAsyncSelectFilter = {
  type: "async-select",
  key: "locality_id",
  label: "Localidad",
  dependsOn: "country_id",
  loadOptions: loadLocalityOptions,
};

export const STATUS_FILTER: AdminStaticSelectFilter = {
  key: "is_active",
  label: "Estado",
  options: { true: "Activo", false: "Inactivo" },
  allLabel: "Todos",
};

export const NEIGHBORHOOD_FILTERS: readonly AdminFilterDefinition[] = [
  COUNTRY_SELECT,
  LOCALITY_SELECT,
  STATUS_FILTER,
  {
    key: "has_geometry",
    label: "Geometría",
    options: { true: "Con geometría", false: "Sin geometría" },
  },
  {
    type: "search",
    key: "search_term",
    label: "Buscar",
    placeholder: "Nombre del barrio",
  },
];

export const LOCALITY_FILTERS: readonly AdminFilterDefinition[] = [
  COUNTRY_SELECT,
  DIVISION_SELECT,
  STATUS_FILTER,
];

export const DIVISION_FILTERS: readonly AdminFilterDefinition[] = [
  COUNTRY_SELECT,
  STATUS_FILTER,
];

export const COUNTRY_FILTERS: readonly AdminFilterDefinition[] = [
  STATUS_FILTER,
  {
    key: "is_supported",
    label: "Soporte",
    options: { true: "Soportado", false: "No soportado" },
    allLabel: "Todos",
  },
];
