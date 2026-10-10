import { ref } from "vue";
import { loadCountryOptions, loadLocalityOptions } from "@/api/admin/catalog";
import type { AdminFilterOptions } from "@/types/admin/filters";
import { logger } from "@/utils/logger";

/** Cascada país → localidad para los formularios admin que crean o cargan en una localidad. */
export function useLocalityPicker() {
  const countryId = ref("");
  const localityId = ref("");
  const countryOptions = ref<AdminFilterOptions>({});
  const localityOptions = ref<AdminFilterOptions>({});
  const loadingLocalities = ref(false);
  const error = ref<string | null>(null);

  async function loadCountries() {
    if (Object.keys(countryOptions.value).length) return;
    try {
      countryOptions.value = await loadCountryOptions();
    } catch (e) {
      error.value = "No se pudieron cargar los países";
      logger.error("locality picker countries failed", e);
    }
  }

  async function loadLocalities(country: string) {
    localityOptions.value = {};
    loadingLocalities.value = country !== "";
    if (!country) return;
    try {
      const options = await loadLocalityOptions({ country_id: country });
      // Si el país cambió mientras llegaba, esta respuesta ya no aplica.
      if (country === countryId.value) localityOptions.value = options;
    } catch (e) {
      if (country !== countryId.value) return;
      error.value = "No se pudieron cargar las localidades";
      logger.error("locality picker localities failed", e);
    } finally {
      if (country === countryId.value) loadingLocalities.value = false;
    }
  }

  /** Arranca con los valores dados (p. ej. los del filtro aplicado) o vacío. */
  function prefill(
    initialCountryId: string | null,
    initialLocalityId: string | null
  ) {
    error.value = null;
    countryId.value = initialCountryId ?? "";
    localityId.value = initialLocalityId ?? "";
    void loadCountries();
    void loadLocalities(countryId.value);
  }

  function onCountryChange() {
    localityId.value = "";
    void loadLocalities(countryId.value);
  }

  return {
    countryId,
    localityId,
    countryOptions,
    localityOptions,
    loadingLocalities,
    error,
    prefill,
    onCountryChange,
  };
}
