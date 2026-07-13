import { ref } from "vue";
import { useRouter } from "vue-router";
import propertiesApi from "@/api/propertiesApi";
import type { PresignedUrlsResponse } from "@/types/properties";

export function useImageUpload() {
  const loading = ref(false);
  const error = ref<string | null>(null);
  const router = useRouter();

  async function uploadImages(files: File[], propertyId: string) {
    loading.value = true;
    error.value = null;
    try {
      const { data } = await propertiesApi.post<PresignedUrlsResponse>(
        "/v1/properties/images/presigned-urls",
        { property_id: propertyId, create_count: files.length }
      );

      const { batch_id, items } = data;

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
        return;
      }

      await propertiesApi.post(`/v1/properties/${propertyId}/images/confirm`, {
        batch_id,
        confirmed_keys,
      });

      router.push("/properties");
    } catch {
      error.value = "Error al subir las imágenes";
    } finally {
      loading.value = false;
    }
  }

  return { loading, error, uploadImages };
}
