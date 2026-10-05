/** Un filtro de `AdminFilterBar`: la `key` es el query param y el campo que espera
 * el backend, y `options` es el `{ value: label }` de `constants/propertyStatus.ts`. */
export interface AdminFilterDefinition {
  key: string;
  label: string;
  options: Readonly<Record<string, string>>;
  /** La opción que quita el filtro; "Todas" si no se pasa. */
  allLabel?: string;
}
