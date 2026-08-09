<template>
  <div class="w-full overflow-x-auto">
    <table class="w-full border-collapse text-sm">
      <thead>
        <tr
          v-for="headerGroup in table.getHeaderGroups()"
          :key="headerGroup.id"
          class="border-b border-brand-divider"
        >
          <th
            v-for="header in headerGroup.headers"
            :key="header.id"
            :class="[
              'py-3 px-4 text-xs font-semibold uppercase tracking-wide text-brand-muted whitespace-nowrap',
              alignOf(header.column.columnDef) === 'right'
                ? 'text-right'
                : 'text-left',
            ]"
          >
            <FlexRender
              :render="header.column.columnDef.header"
              :props="header.getContext()"
            />
          </th>
        </tr>
      </thead>

      <tbody>
        <!-- Excluyentes a propósito: con las dos clases el hover le gana al seleccionado y lo despinta. -->
        <tr
          v-for="row in table.getRowModel().rows"
          :key="row.id"
          @click="emit('rowClick', row.original)"
          :class="[
            'border-b border-brand-divider last:border-0 transition-colors',
            isSelectable ? 'cursor-pointer' : '',
            isSelected(row.original)
              ? 'bg-brand-primary-light'
              : 'hover:bg-brand-bg',
          ]"
        >
          <td
            v-for="cell in row.getVisibleCells()"
            :key="cell.id"
            :class="[
              'py-3 px-4 text-brand-text align-middle',
              alignOf(cell.column.columnDef) === 'right'
                ? 'text-right'
                : 'text-left',
            ]"
          >
            <!-- Cada slot se llama como su columna y gana sobre FlexRender; sin prefijo para no forzar `#[...]`. -->
            <slot
              :name="cell.column.id"
              :row="row.original"
              :value="cell.getValue()"
            >
              <FlexRender
                :render="cell.column.columnDef.cell"
                :props="cell.getContext()"
              />
            </slot>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="loading" class="py-10 flex justify-center">
      <BaseSpinner class="h-6 w-6 text-brand-primary" />
    </div>

    <EmptyState
      v-else-if="!table.getRowModel().rows.length"
      :title="emptyTitle"
      :description="emptyDescription"
    />
  </div>
</template>

<script setup lang="ts" generic="T">
import { computed } from "vue";
import {
  FlexRender,
  getCoreRowModel,
  useVueTable,
  type ColumnDef,
} from "@tanstack/vue-table";
import BaseSpinner from "@/components/shared/BaseSpinner.vue";
import EmptyState from "@/components/shared/EmptyState.vue";

const props = withDefaults(
  defineProps<{
    columns: ColumnDef<T, any>[]; // eslint-disable-line @typescript-eslint/no-explicit-any
    data: T[];
    loading?: boolean;
    emptyTitle?: string;
    emptyDescription?: string;
    /** Sin `rowKey` la tabla no es seleccionable: no hay con qué comparar. */
    rowKey?: (row: T) => string;
    selectedKey?: string | null;
  }>(),
  {
    loading: false,
    emptyTitle: "Nada por acá",
    emptyDescription: "No hay resultados para los filtros seleccionados.",
    rowKey: undefined,
    selectedKey: null,
  }
);

const emit = defineEmits<{ rowClick: [row: T] }>();

const isSelectable = computed(() => props.rowKey !== undefined);

function isSelected(row: T): boolean {
  if (!props.rowKey || props.selectedKey == null) return false;
  return props.rowKey(row) === props.selectedKey;
}

/** Getters para que reaccione a las props; solo core row model, porque orden y paginación son server-side. */
const table = useVueTable({
  get data() {
    return props.data;
  },
  get columns() {
    return props.columns;
  },
  getCoreRowModel: getCoreRowModel(),
});

type ColumnAlign = "left" | "right";

function alignOf(columnDef: { meta?: unknown }): ColumnAlign {
  const meta = columnDef.meta as { align?: ColumnAlign } | undefined;
  return meta?.align ?? "left";
}
</script>
