import type { RowData } from "@tanstack/vue-table";
import type { ColumnAlign } from "@/types/shared/ui";

// `meta` de las columnas tipado para toda la app, como propone TanStack.
declare module "@tanstack/vue-table" {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  interface ColumnMeta<TData extends RowData, TValue> {
    align?: ColumnAlign;
  }
}
