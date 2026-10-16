import type {
  CountryFormValues,
  DivisionFormValues,
  LocalityFormValues,
} from "@/types/admin/catalog";
import { isValidTimeZone } from "@/utils/timezone";

const inRange = (value: number | "", limit: number): value is number =>
  typeof value === "number" && Math.abs(value) <= limit;

// El backend no valida rango ni zona horaria: se exige acá.
export function isLocalityFormValid(form: LocalityFormValues): boolean {
  return (
    form.name.trim() !== "" &&
    isValidTimeZone(form.timezone.trim()) &&
    inRange(form.latitude, 90) &&
    inRange(form.longitude, 180)
  );
}

export function isDivisionFormValid(form: DivisionFormValues): boolean {
  return form.name.trim() !== "" && form.typeName.trim() !== "";
}

export function isCountryFormValid(form: CountryFormValues): boolean {
  return (
    form.name.trim() !== "" &&
    form.phoneCode.trim() !== "" &&
    /^[A-Za-z]{3}$/.test(form.currencyCode.trim()) &&
    form.defaultLocale.trim() !== "" &&
    isValidTimeZone(form.defaultTimezone.trim())
  );
}

// ISO 3166-1: dos y tres letras, tres dígitos.
export function isIsoCodeValid(iso: {
  alpha2: string;
  alpha3: string;
  numeric: string;
}): boolean {
  return (
    /^[A-Za-z]{2}$/.test(iso.alpha2.trim()) &&
    /^[A-Za-z]{3}$/.test(iso.alpha3.trim()) &&
    /^\d{3}$/.test(iso.numeric.trim())
  );
}

/** Los campos editables del país, normalizados, para el body de crear o editar. */
export function toCountryFields(form: CountryFormValues) {
  return {
    name: form.name.trim(),
    official_name: form.officialName.trim() || null,
    native_name: form.nativeName.trim() || null,
    phone_code: form.phoneCode.trim(),
    currency_code: form.currencyCode.trim().toUpperCase(),
    default_locale: form.defaultLocale.trim(),
    default_timezone: form.defaultTimezone.trim(),
    is_supported: form.isSupported,
  };
}
