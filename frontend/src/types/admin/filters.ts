/** Opciones de un select como `{ value: label }`. */
export type AdminFilterOptions = Readonly<Record<string, string>>;

interface AdminFilterBase {
  /** El query param, con el nombre que espera el backend. */
  key: string;
  label: string;
  /** La opción que quita el filtro; "Todas" si no se pasa. */
  allLabel?: string;
}

export interface AdminStaticSelectFilter extends AdminFilterBase {
  type?: "select";
  options: AdminFilterOptions;
}

export interface AdminAsyncSelectFilter extends AdminFilterBase {
  type: "async-select";
  /** Key del filtro padre: sin valor ahí, este queda vacío y deshabilitado. */
  dependsOn?: string;
  loadOptions: (parents: Record<string, string>) => Promise<AdminFilterOptions>;
}

export interface AdminSearchFilter extends AdminFilterBase {
  type: "search";
  placeholder?: string;
}

export type AdminFilterDefinition =
  | AdminStaticSelectFilter
  | AdminAsyncSelectFilter
  | AdminSearchFilter;
