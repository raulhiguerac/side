import { loadCountryOptions, loadLocalityOptions } from "@/api/admin/catalog";
import type { AdminFilterDefinition } from "@/types/admin/filters";

// País y localidad usan los GET públicos (solo activos) hasta tener los admin.
export const NEIGHBORHOOD_FILTERS: readonly AdminFilterDefinition[] = [
  {
    type: "async-select",
    key: "country_id",
    label: "País",
    allLabel: "Todos",
    loadOptions: loadCountryOptions,
  },
  {
    type: "async-select",
    key: "locality_id",
    label: "Localidad",
    dependsOn: "country_id",
    loadOptions: loadLocalityOptions,
  },
  {
    key: "is_active",
    label: "Estado",
    options: { true: "Activo", false: "Inactivo" },
    allLabel: "Todos",
  },
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
