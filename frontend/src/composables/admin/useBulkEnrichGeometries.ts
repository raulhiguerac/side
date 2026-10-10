import { ref } from "vue";
import axios from "axios";
import * as adminCatalogApi from "@/api/admin/catalog";
import type { BulkGeometriesResult } from "@/types/admin/catalog";
import { logger } from "@/utils/logger";

function messageForError(error: unknown): string {
  if (!axios.isAxiosError(error)) return "No se pudieron cargar las geometrías";
  if (error.code === "ECONNABORTED")
    return "El servidor tardó demasiado. Prueba con un archivo más chico.";

  const code = error.response?.data?.code;
  if (code === "FILE_TOO_LARGE")
    return "El archivo supera el tamaño permitido.";
  if (code === "UNSUPPORTED_FILE_TYPE")
    return "El tipo de archivo no está permitido.";
  // Sin `code`: lo lanza la ruta cuando el archivo no es JSON.
  if (error.response?.status === 422) return "El archivo no es un JSON válido.";
  if (code === "CATALOG_ADMIN_DB_UNAVAILABLE")
    return "El catálogo no está disponible. Intenta de nuevo en un momento.";
  if (error.response?.status === 403)
    return "No tienes permisos para cargar barrios";

  return "No se pudieron cargar las geometrías";
}

/** Sube un FeatureCollection y asigna cada Feature al barrio con ese nombre. */
export function useBulkEnrichGeometries() {
  const saving = ref(false);
  const error = ref<string | null>(null);

  async function upload(
    localityId: string,
    file: File,
    nameField: string
  ): Promise<BulkGeometriesResult | null> {
    reset();
    saving.value = true;
    try {
      return await adminCatalogApi.bulkEnrichNeighborhoodGeometries(
        localityId,
        file,
        nameField
      );
    } catch (e) {
      logger.error("admin bulk geometries failed", e);
      error.value = messageForError(e);
      return null;
    } finally {
      saving.value = false;
    }
  }

  function reset() {
    error.value = null;
  }

  return {
    saving,
    error,
    upload,
    reset,
  };
}
