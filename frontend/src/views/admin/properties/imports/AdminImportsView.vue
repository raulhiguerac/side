<template>
  <div>
    <div class="mb-6 flex justify-end">
      <BaseButton @click="isBulkModalOpen = true" class="whitespace-nowrap">
        <Upload class="h-4 w-4" />
        Importar CSV
      </BaseButton>
    </div>

    <AdminSplitView :error="error">
      <template #filters>
        <AdminFilterBar
          :filters="BULK_JOB_FILTERS"
          :initial="urlFilters"
          :loading="loading"
          @apply="pushFilters"
        />
      </template>

      <template #table>
        <AdminBulkJobsTable
          :rows="jobs"
          :loading="loading"
          :selected-id="selectedId"
          @row-click="selectedId = $event.id"
        />
      </template>

      <template #footer>
        <AdminPaginationFooter
          :range="range"
          :total="total"
          :has-prev="hasPrev"
          :has-next="hasNext"
          @prev="prev"
          @next="next"
        />
      </template>

      <template #panel>
        <AdminBulkJobPanel :job="selectedJob" />
      </template>
    </AdminSplitView>

    <BulkUploadPropertiesModal v-model="isBulkModalOpen" />
  </div>
</template>

<script lang="ts" setup>
import BaseButton from "@/components/shared/BaseButton.vue";
import { computed, ref } from "vue";
import { Upload } from "@lucide/vue";
import AdminPaginationFooter from "@/components/admin/shared/AdminPaginationFooter.vue";
import AdminSplitView from "@/components/admin/shared/AdminSplitView.vue";
import AdminFilterBar from "@/components/admin/shared/AdminFilterBar.vue";
import AdminBulkJobsTable from "@/components/admin/properties/imports/AdminBulkJobsTable.vue";
import AdminBulkJobPanel from "@/components/admin/properties/imports/AdminBulkJobPanel.vue";
import BulkUploadPropertiesModal from "@/components/admin/properties/imports/BulkUploadPropertiesModal.vue";
import { useBulkJobs } from "@/composables/admin/useBulkJobs";
import { useRowSelection } from "@/composables/admin/useRowSelection";
import { useUrlFilters } from "@/composables/admin/useUrlFilters";
import { BULK_JOB_FILTERS } from "@/constants/propertiesFilters";

const isBulkModalOpen = ref(false);

const {
  jobs,
  total,
  range,
  hasPrev,
  hasNext,
  loading,
  error,
  applyFilters,
  next,
  prev,
} = useBulkJobs();

const { selectedId } = useRowSelection(jobs);

// Fila entera: `expires_at` y el estado deciden si se puede relanzar.
const selectedJob = computed(
  () => jobs.value.find((job) => job.id === selectedId.value) ?? null
);

const { urlFilters, pushFilters } = useUrlFilters(
  BULK_JOB_FILTERS,
  applyFilters
);
</script>
