import { ref } from "vue";
import axios from "axios";
import * as adminCatalogApi from "@/api/admin/catalog";
import type { NeighborhoodAdminResponse } from "@/types/admin/catalog";
import { logger } from "@/utils/logger";

function messageForError(error: unknown): string {
  if (!axios.isAxiosError(error)) return "No se pudo subir la geometría";

  const code = error.response?.data?.code;
  if (code === "NEIGHBORHOOD_INVALID_GEOMETRY")
    return "El archivo debe tener un Polygon o MultiPolygon, solo o en un Feature.";
  if (code === "NEIGHBORHOOD_ADMIN_NOT_FOUND")
    return "El barrio ya no existe. Recarga la lista.";
  if (code === "FILE_TOO_LARGE") return "El archivo supera los 5 MB.";
  if (code === "UNSUPPORTED_FILE_TYPE")
    return "Solo se aceptan archivos .geojson o .json.";
  if (code === "CATALOG_ADMIN_DB_UNAVAILABLE")
    return "El catálogo no está disponible. Intenta de nuevo en un momento.";
  if (error.response?.status === 403)
    return "No tienes permisos para editar barrios";
  // Sin `code`: lo lanza la ruta cuando el archivo no es JSON.
  if (error.response?.status === 422) return "El archivo no es un JSON válido.";

  return "No se pudo subir la geometría";
}

/** POST multipart del GeoJSON de un barrio; reemplaza la geometría y sus celdas H3. */
export function useReplaceNeighborhoodGeometry() {
  const saving = ref(false);
  const error = ref<string | null>(null);

  async function replace(
    neighborhoodId: string,
    file: File
  ): Promise<NeighborhoodAdminResponse | null> {
    reset();
    saving.value = true;
    try {
      return await adminCatalogApi.replaceNeighborhoodGeometry(
        neighborhoodId,
        file
      );
    } catch (e) {
      logger.error("admin neighborhood geometry upload failed", e);
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
    replace,
    reset,
  };
}
