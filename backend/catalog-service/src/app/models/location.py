"""
=============================================================================
MODELOS GEOGRAFICOS - SOURCE OF TRUTH
=============================================================================

Estructura jerárquica simple (un solo nivel administrativo):

    Country (ISO 3166-1)
        └── AdminDivision (departamento/estado/región)
                └── Locality (municipio/ciudad)
                        └── Neighborhood (barrio, opcional)

    PointOfInterest (POI) → referencia Locality y opcionalmente Neighborhood

Ejemplos por país:
- Colombia: Country → Departamento → Municipio (Locality) → Barrio
- USA: Country → State → City (Locality) → Neighborhood
- España: Country → Comunidad Autónoma → Municipio (Locality) → Barrio
- México: Country → Estado → Municipio (Locality) → Colonia
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, VARCHAR
from sqlalchemy.sql import func
from sqlmodel import Field, Relationship, SQLModel

# =============================================================================
# MIXINS
# =============================================================================


class AuditMixin(SQLModel):
    """Campos de auditoría para todas las entidades."""

    created_at: datetime = Field(                                                                                                         
        sa_type=DateTime(timezone=True),                                                                                                  
            sa_column_kwargs={                                                                                                                
                "server_default": func.now(),                                                                                                 
                "nullable": False,                                                                                                            
            }                                                                                                                                 
        )                                                                                                                                     
    updated_at: datetime = Field(                                                                                                         
        sa_type=DateTime(timezone=True),                                                                                                  
            sa_column_kwargs={                                                                                                                
                "server_default": func.now(),                                                                                                 
                "onupdate": func.now(),                                                                                                       
                "nullable": False,                                                                                                            
            }                                                                                                                                 
        )
    created_by: Optional[uuid.UUID] = Field(default=None)
    updated_by: Optional[uuid.UUID] = Field(default=None)


# =============================================================================
# COUNTRY - ISO 3166-1
# =============================================================================


class Country(AuditMixin, SQLModel, table=True):
    """
    País según ISO 3166-1.

    Fuente de datos: https://www.iso.org/iso-3166-country-codes.html
    """

    __tablename__ = "countries"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # ISO 3166-1 codes
    iso_alpha2: str = Field(
        max_length=2, nullable=False, unique=True, index=True
    )  # "CO"
    iso_alpha3: str = Field(max_length=3, nullable=False, unique=True)  # "COL"
    iso_numeric: str = Field(max_length=3, nullable=False, unique=True)  # "170"

    # Names
    name: str = Field(max_length=100, nullable=False)  # "Colombia"
    official_name: Optional[str] = Field(
        max_length=200, default=None
    )  # "Republic of Colombia"
    native_name: Optional[str] = Field(max_length=100, default=None)  # "Colombia"

    # Metadata
    phone_code: str = Field(max_length=8, nullable=False)  # "+57"
    currency_code: str = Field(max_length=3, nullable=False)  # "COP" (ISO 4217)
    default_locale: str = Field(max_length=10, default="es")  # "es", "en", "pt"
    default_timezone: str = Field(
        max_length=64, nullable=False
    )  # "America/Bogota"

    # Control
    is_active: bool = Field(default=True, nullable=False)
    is_supported: bool = Field(
        default=False, nullable=False
    )  # Si el sistema lo soporta activamente


# =============================================================================
# ADMIN DIVISION - Nivel administrativo (ISO 3166-2 compatible)
# =============================================================================


class AdminDivision(AuditMixin, SQLModel, table=True):
    """
    División administrativa de primer nivel.

    Representa el nivel inmediatamente debajo del país:
    - Colombia: Departamento
    - USA: State
    - España: Comunidad Autónoma
    - México: Estado

    Sin recursión. Un solo nivel.
    """

    __tablename__ = "admin_divisions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    country_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("countries.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )

    # Identificadores
    code: str = Field(
        max_length=20, nullable=False, index=True
    )  # Código local (DANE, FIPS, INSEE)
    iso_code: Optional[str] = Field(
        max_length=10, default=None
    )  # ISO 3166-2: "CO-CUN", "US-CA"

    # Nombres
    name: str = Field(max_length=150, nullable=False)  # "Cundinamarca"
    type_name: str = Field(
        max_length=50, nullable=False
    )  # "Departamento", "State", "Comunidad Autónoma"

    # Control
    is_active: bool = Field(default=True, nullable=False)

    __table_args__ = (
        # Código único por país
        UniqueConstraint("country_id", "code", name="uq_admin_div_country_code"),
        # ISO code único global si existe
        Index(
            "ix_admin_div_iso_code",
            "iso_code",
            unique=True,
            postgresql_where="iso_code IS NOT NULL",
        ),
    )


# =============================================================================
# LOCALITY - Lugar poblado (ciudad, pueblo, villa)
# =============================================================================


class LocalityType(str, Enum):
    """Tipo de localidad según tamaño/importancia."""

    city = "city"      # Ciudad grande (>100k hab)
    town = "town"      # Pueblo/ciudad pequeña
    village = "village"  # Vereda/corregimiento/villa


class Locality(AuditMixin, SQLModel, table=True):
    """
    Municipio o lugar poblado.

    En la mayoría de países latinoamericanos, esto ES el municipio.
    El tipo (city/town/village) indica el tamaño, no la clasificación
    administrativa.

    Ejemplos:
    - Bogotá D.C. → city
    - Zipaquirá → town
    - Choachí → village
    """

    __tablename__ = "localities"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    country_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("countries.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )
    admin_division_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("admin_divisions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )

    # Relationships
    admin_division: Optional["AdminDivision"] = Relationship()

    # Identificadores
    code: str = Field(
        max_length=20, nullable=False, index=True
    )  # Código oficial local

    # Nombres
    name: str = Field(max_length=150, nullable=False)
    local_name: Optional[str] = Field(max_length=150, default=None)
    search_name: str = Field(
        max_length=150, nullable=False, index=True
    )  # Normalizado: "medellin"

    # Clasificación
    locality_type: LocalityType = Field(default=LocalityType.city, nullable=False)

    # Geografía
    latitude: float = Field(nullable=False)
    longitude: float = Field(nullable=False)
    timezone: str = Field(max_length=64, nullable=False)

    # Control
    is_active: bool = Field(default=True, nullable=False)
    is_capital: bool = Field(default=False, nullable=False)  # Capital del admin_division

    __table_args__ = (
        UniqueConstraint("country_id", "code", name="uq_locality_country_code"),
        Index("ix_locality_coords", "latitude", "longitude"),
    )


# =============================================================================
# NEIGHBORHOOD - Barrio/Zona (con geometría de polígono)
# =============================================================================


class Neighborhood(AuditMixin, SQLModel, table=True):
    """
    Barrio o zona dentro de una localidad.

    Este nivel es opcional y generalmente solo existe para ciudades grandes.
    Incluye geometría de polígono para queries espaciales (point-in-polygon).
    """

    __tablename__ = "neighborhoods"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    locality_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("localities.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )

    # Relationships
    locality: Optional["Locality"] = Relationship()

    # Identificadores
    code: str = Field(max_length=30, nullable=False, index=True)
    postal_code: Optional[str] = Field(max_length=20, default=None, index=True)

    # Nombres
    name: str = Field(max_length=150, nullable=False)
    search_name: str = Field(max_length=150, nullable=False)  # Normalizado

    # Geografía
    latitude: float = Field(nullable=False)  # Centroide
    longitude: float = Field(nullable=False)  # Centroide
    geom: Optional[bytes] = Field(
        sa_column=Column(
            Geometry(geometry_type="MULTIPOLYGON", srid=4326),
            nullable=True,  # Algunos barrios no tienen polígono definido
        ),
        default=None,
    )
    h3_cells: Optional[list[str]] = Field(
        sa_column=Column(ARRAY(VARCHAR(16)), nullable=True),
        default=None,
    )  # Celdas H3 resolution 9 (~300m) que cubren el polígono. Poblado gradualmente con tráfico.

    # Control
    is_active: bool = Field(default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("locality_id", "code", name="uq_neighborhood_locality_code"),
        Index("ix_neighborhood_geom", "geom", postgresql_using="gist"),
        Index("ix_neighborhood_h3_cells", "h3_cells", postgresql_using="gin"),
    )


# =============================================================================
# POINT OF INTEREST - POI con cache-aside (provider-agnostic)
# =============================================================================


class PoiSource(str, Enum):
    """Origen del dato del POI."""

    osm = "osm"        # Obtenido via Overpass API (OpenStreetMap)
    manual = "manual"  # Creado manualmente
    seed = "seed"      # Carga inicial / seed data


class PointOfInterest(AuditMixin, SQLModel, table=True):
    """
    Punto de interés (POI).

    Funciona como cache persistente con estrategia cache-aside:
        Request → Redis → PostgreSQL (esta tabla) → Provider API

    El campo `external_id` + `source` permite deduplicar y evitar llamadas repetidas.
    El campo `raw_response` almacena el response completo del proveedor para
    extraer campos adicionales sin re-fetch.
    """

    __tablename__ = "points_of_interest"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    locality_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("localities.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )
    neighborhood_id: Optional[uuid.UUID] = Field(
        sa_column=Column(
            ForeignKey("neighborhoods.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        )
    )

    # Relationships
    locality: Optional["Locality"] = Relationship()
    neighborhood: Optional["Neighborhood"] = Relationship()

    # Provider / cache-aside
    external_id: Optional[str] = Field(max_length=255, default=None, index=True)
    source: PoiSource = Field(default=PoiSource.osm, nullable=False)
    raw_response: Optional[dict] = Field(
        sa_column=Column(JSON, nullable=True),
        default=None,
    )
    fetched_at: Optional[datetime] = Field(
        sa_type=DateTime(timezone=True),
        default=None,
    )
    is_stale: bool = Field(default=False, nullable=False)

    # Datos del POI
    name: str = Field(max_length=255, nullable=False)
    search_name: str = Field(max_length=255, nullable=False, index=True)
    full_address: Optional[str] = Field(max_length=500, default=None)
    category: Optional[str] = Field(max_length=100, default=None, index=True)
    subcategories: Optional[list[str]] = Field(
        sa_column=Column(ARRAY(VARCHAR(100)), nullable=True),
        default=None,
    )

    # Geografía
    latitude: float = Field(nullable=False)
    longitude: float = Field(nullable=False)
    h3_index: str = Field(max_length=16, nullable=False, index=True)  # Precomputado: h3.latlng_to_cell(lat, lon, res=9)
    geom: Optional[bytes] = Field(
        sa_column=Column(
            Geometry(geometry_type="POINT", srid=4326),
            nullable=True,
        ),
        default=None,
    )

    # Contacto
    phone: Optional[str] = Field(max_length=50, default=None)
    website: Optional[str] = Field(max_length=500, default=None)

    # Control
    is_active: bool = Field(default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("external_id", "source", name="uq_poi_external_id_source"),
        Index("ix_poi_coords", "latitude", "longitude"),
        Index("ix_poi_geom", "geom", postgresql_using="gist"),
    )


# =============================================================================
# FETCH ZONE - Registro de celdas ya fetcheadas desde provider externo
# =============================================================================


class FetchZone(AuditMixin, SQLModel, table=True):
    """
    Registro de celdas H3 resolution 9 (~300m) ya consultadas al proveedor de POIs.

    Permite saber si una zona ya fue poblada y cuándo, sin recalcular
    aggregates espaciales en cada request. El batch nocturno itera esta
    tabla para decidir qué zonas refrescar.
    """

    __tablename__ = "fetch_zones"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    locality_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("localities.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )

    # H3 resolution 9 (~300m)
    h3_index: str = Field(max_length=16, nullable=False, unique=True, index=True)

    # Métricas de fetch
    poi_count: int = Field(default=0, nullable=False)
    fetched_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),
            "nullable": False,
        },
    )
    is_stale: bool = Field(default=False, nullable=False, index=True)
