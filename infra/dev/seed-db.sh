#!/bin/sh
# Restaura los dumps de infra/seeds/ en la DB de cada servicio.
# Idempotente por omision: si la tabla centinela ya tiene filas, salta ese dump
# entero. No trunca nada a proposito — un seed no deberia poder borrar datos.
# Corre despues de que cada servicio aplico sus migraciones: los dumps son
# --data-only y asumen el esquema ya creado.
set -eu

seed () { # $1 dsn  $2 dump  $3 tabla centinela
  name=$(basename "$2")
  if [ ! -f "$2" ]; then
    echo "  ERROR: falta $name. Corriste 'make bootstrap'?" >&2
    exit 1
  fi
  n=$(psql "$1" -tAc "SELECT count(*) FROM $3")
  if [ "$n" != "0" ]; then
    echo "  skip   $name — $3 ya tiene $n filas"
    return 0
  fi
  echo "  carga  $name -> $3"
  zcat "$2" | psql "$1" -v ON_ERROR_STOP=1 -q
}

echo "seed-db:"
seed "$DATABASE_CATALOG_URL"    /seeds/catalog_geo.sql.gz   neighborhoods
seed "$DATABASE_CATALOG_URL"    /seeds/catalog_pois.sql.gz  points_of_interest
seed "$DATABASE_PROPERTIES_URL" /seeds/properties.sql.gz    properties
seed "$DATABASE_URL"            /seeds/users.sql.gz         accounts
echo "seed-db: ok"
