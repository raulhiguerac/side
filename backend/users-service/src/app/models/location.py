import uuid
from typing import Optional

from sqlmodel import Field, SQLModel

from sqlalchemy import UniqueConstraint

class Country(SQLModel, table=True):

    __tablename__ = "country"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    name: str = Field(unique=True, nullable=False)
    iso2: str = Field(unique=True, nullable=False)
    iso3: str = Field(unique=True, nullable=False)
    phone_code: str = Field(nullable=False)
    currency: str = Field(nullable=False)
    is_active: bool = Field(nullable=False)

class City(SQLModel, table=True):

    __tablename__ = "city"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    country_id: uuid.UUID = Field(foreign_key="country.id", index=True)
    name: str = Field(nullable=False)
    state_id: str = Field(nullable=False)
    code: str = Field(nullable=False)
    latitude: float  = Field(nullable=False)
    longitude: float = Field(nullable=False)
    is_active: bool = Field(nullable=False)
    timezone: str = Field(nullable=False)

    __table_args__ = (
        UniqueConstraint("country_id", "code", name="uq_city_country_id_code"),
    )

class Neighborhood(SQLModel, table=True):

    __tablename__ = "neighborhood"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    city_id: uuid.UUID = Field(foreign_key="city.id", index=True)
    name: str = Field(max_length=150, nullable=False)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    latitude: float = Field(nullable=False)
    longitude: float = Field(nullable=False)
    is_active: bool = Field(default=True)

    __table_args__ = (
        UniqueConstraint("city_id", "name", name="uq_neighborhood_city_id_name"),
    )