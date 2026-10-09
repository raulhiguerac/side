import { ref } from "vue";
import * as propertiesApi from "@/api/properties";

export function useImageUpload() {
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function uploadImages(
    files: File[],
    propertyId: string
  ): Promise<boolean> {
    loading.value = true;
    error.value = null;
    try {
      const { batch_id, items } = await propertiesApi.requestImageUploadUrls(
        propertyId,
        files.length
      );

      const results = await Promise.allSettled(
        items.map((item, i) =>
          fetch(item.upload_url, {
            method: "PUT",
            body: files[i],
            headers: { "Content-Type": files[i].type },
          })
        )
      );

      const confirmed_keys = items
        .filter((_, i) => {
          const r = results[i];
          return r.status === "fulfilled" && r.value.ok;
        })
        .map((item) => item.key);

      if (confirmed_keys.length === 0) {
        error.value = "No se pudo subir ninguna imagen";
        return false;
      }

      await propertiesApi.confirmImageUploads(
        propertyId,
        batch_id,
        confirmed_keys
      );

      return true;
    } catch {
      error.value = "Error al subir las imágenes";
      return false;
    } finally {
      loading.value = false;
    }
  }

  return { loading, error, uploadImages };
}
