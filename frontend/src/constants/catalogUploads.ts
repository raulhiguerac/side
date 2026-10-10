import type { FileRequirement } from "@/types/shared/ui";

interface UploadSpec {
  extensions: readonly string[];
  maxSizeMb: number;
  requirements: readonly FileRequirement[];
}

// Extensiones y tope de `core/files/policies.py` de catalog-service.
export const GEOMETRY_UPLOAD: UploadSpec = {
  extensions: [".geojson", ".json"],
  maxSizeMb: 5,
  requirements: [
    { text: "Archivo .geojson o .json, de hasta 5 MB", accepted: true },
    {
      text: "Un solo polígono (Polygon o MultiPolygon), suelto o en un Feature",
      accepted: true,
    },
    {
      text: "No se acepta un FeatureCollection, aunque tenga un solo barrio",
      accepted: false,
    },
  ],
};

export const BULK_NEIGHBORHOODS_UPLOAD: UploadSpec = {
  extensions: [".csv", ".json", ".txt"],
  maxSizeMb: 10,
  requirements: [
    { text: "Archivo .csv, .json o .txt, de hasta 10 MB", accepted: true },
    { text: "Columnas: code, name, latitude, longitude", accepted: true },
    { text: "Opcionales: postal_code, is_active", accepted: true },
  ],
};

export const BULK_GEOMETRIES_UPLOAD: UploadSpec = {
  extensions: [".geojson", ".json"],
  maxSizeMb: 50,
  requirements: [
    { text: "Archivo .geojson o .json, de hasta 50 MB", accepted: true },
    {
      text: "Un FeatureCollection con un Feature por barrio",
      accepted: true,
    },
    {
      text: "Cada Feature se empareja por el nombre del barrio",
      accepted: true,
    },
  ],
};
