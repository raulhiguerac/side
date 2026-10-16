import type { Geometry } from "geojson";
import type { Bbox } from "@/types/maps/base";
import type { AdminPage } from "@/types/shared/pagination";
import type {
  AdminDivisionResponse,
  BulkCreateNeighborhoodsResult,
  BulkEnrichNeighborhoodGeometriesResult,
  CreateAdminDivisionRequest,
  CreateCountryRequest,
  CountryResponse,
  CreateLocalityRequest,
  GetAllAdminDivisionsPage,
  GetAllCountriesPage,
  GetAllCountriesResponse,
  CreateNeighborhoodRequest,
  GetAllLocalitiesPage,
  GetAllLocalitiesResponse,
  LocalityAdminResponse as GeneratedLocalityAdminResponse,
  LocalityType as GeneratedLocalityType,
  UpdateAdminDivisionRequest,
  UpdateCountryRequest,
  UpdateLocalityRequest,
  NeighborhoodAdminResponse as GeneratedNeighborhoodAdminResponse,
  UpdateNeighborhoodRequest,
} from "@/types/generated/catalog";

/** Fila de `GET /v1/admin/neighborhoods`: `svg_path` y `bbox` vienen nulos si el barrio no tiene geometría. */
export interface NeighborhoodAdminRow {
  id: string;
  locality_id: string;
  code: string;
  name: string;
  is_active: boolean;
  has_geometry: boolean;
  svg_path: string | null;
  bbox: Bbox | null;
}

export interface NeighborhoodCoverage {
  with_geometry: number;
  total: number;
}

export interface NeighborhoodAdminPage extends AdminPage<NeighborhoodAdminRow> {
  coverage: NeighborhoodCoverage;
}

/** Filtros que acepta `ListNeighborhoodsAdminRequest`; llegan como string desde la URL. */
export interface NeighborhoodAdminFilters {
  locality_id?: string;
  is_active?: string;
  has_geometry?: string;
  search_term?: string;
}

/** `GET /v1/admin/neighborhoods/{id}`: GeoJSON simplificado (~1,1 m) y área sobre la geometría original. */
export interface NeighborhoodAdminDetail {
  id: string;
  locality_id: string;
  code: string;
  name: string;
  postal_code: string | null;
  latitude: number;
  longitude: number;
  is_active: boolean;
  geometry: Geometry | null;
  area_m2: number | null;
}

/** Un vecino de `GET /v1/admin/neighborhoods/geometries`, ya recortado al bbox pedido. */
export interface NeighborhoodGeometryItem {
  id: string;
  name: string;
  geometry: Geometry;
}

export type NeighborhoodAction = "edit" | "geometry" | "status";

/** Resultado del CSV de barrios: `errors` trae los nombres que no se guardaron. */
export type BulkNeighborhoodsResult = BulkCreateNeighborhoodsResult;

/** Resultado del GeoJSON en bloque: `unmatched` son barrios de la localidad sin Feature. */
export type BulkGeometriesResult = BulkEnrichNeighborhoodGeometriesResult;

/** Body de `POST /v1/admin/neighborhoods`: sin geometría, se sube aparte. */
export type NeighborhoodCreatePayload = CreateNeighborhoodRequest;

/** Body de `PATCH /v1/admin/neighborhoods/{id}`: solo se aplica lo que viaja. */
export type NeighborhoodUpdatePayload = UpdateNeighborhoodRequest;

/** Respuesta del PATCH: sin geometría ni área. */
export type NeighborhoodAdminResponse = GeneratedNeighborhoodAdminResponse;

/** Fila de `GET /v1/admin/localities`: trae los ids de país y división para la cascada. */
export type LocalityAdminRow = GetAllLocalitiesResponse;

export type LocalityAdminPage = GetAllLocalitiesPage;

export type LocalityType = GeneratedLocalityType;

/** Filtros que acepta `GetAllLocalitiesRequest`; llegan como string desde la URL. */
export interface LocalityAdminFilters {
  country_id?: string;
  admin_division_id?: string;
  is_active?: string;
}

export type LocalityAction = "edit" | "status" | "neighborhoods";

/** Body de `POST /v1/admin/localities`. */
export type LocalityCreatePayload = CreateLocalityRequest;

/** Body de `PATCH /v1/admin/localities/{id}`: código, país y división no se editan. */
export type LocalityUpdatePayload = UpdateLocalityRequest;

export type LocalityAdminResponse = GeneratedLocalityAdminResponse;

/** Estado de `LocalityFormFields`; lat/lng quedan en "" mientras el input esté vacío. */
export interface LocalityFormValues {
  name: string;
  localName: string;
  localityType: LocalityType;
  timezone: string;
  latitude: number | "";
  longitude: number | "";
  isCapital: boolean;
}

/** Fila de `GET /v1/admin/admin-divisions`. */
export type DivisionAdminRow = AdminDivisionResponse;

export type DivisionAdminPage = GetAllAdminDivisionsPage;

/** Filtros que acepta `GetAllAdminDivisionsRequest`; llegan como string desde la URL. */
export interface DivisionAdminFilters {
  country_id?: string;
  is_active?: string;
}

export type DivisionAction = "edit" | "status" | "localities";

/** Body de `POST /v1/admin/admin-divisions`. */
export type DivisionCreatePayload = CreateAdminDivisionRequest;

/** Body de `PATCH /v1/admin/admin-divisions/{id}`: código y país no se editan. */
export type DivisionUpdatePayload = UpdateAdminDivisionRequest;

/** Estado de `DivisionFormFields`. */
export interface DivisionFormValues {
  name: string;
  typeName: string;
  isoCode: string;
}

/** Fila de `GET /v1/admin/countries`: trae todos los campos del modelo. */
export type CountryAdminRow = GetAllCountriesResponse;

export type CountryAdminPage = GetAllCountriesPage;

/** Filtros que acepta `GetAllCountriesRequest`; llegan como string desde la URL. */
export interface CountryAdminFilters {
  is_active?: string;
  is_supported?: string;
}

export type CountryAction = "edit" | "status" | "divisions";

/** Body de `POST /v1/admin/countries`. */
export type CountryCreatePayload = CreateCountryRequest;

/** Body de `PATCH /v1/admin/countries/{id}`: los códigos ISO no se editan. */
export type CountryUpdatePayload = UpdateCountryRequest;

/** Respuesta de `POST`/`PATCH` de países: un subconjunto de la fila. */
export type CountryAdminResponse = CountryResponse;

/** Estado de `CountryFormFields`. */
export interface CountryFormValues {
  name: string;
  officialName: string;
  nativeName: string;
  phoneCode: string;
  currencyCode: string;
  defaultLocale: string;
  defaultTimezone: string;
  isSupported: boolean;
}
