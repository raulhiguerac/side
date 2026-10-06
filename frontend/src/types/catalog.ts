/** Ítem mínimo de los `GET` públicos de catálogo (país, localidad, barrio). */
export interface CatalogItem {
  id: string;
  name: string;
}

export interface Locality extends CatalogItem {
  admin_division: CatalogItem;
}
