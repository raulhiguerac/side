import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# src/ directory so that `app.*` imports resolve correctly.
# The models import each other as `app.models.*`, so importing them as bare
# `models.*` would load every one of them twice under two module identities and
# register each table in SQLModel.metadata twice.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlmodel import SQLModel

from app.models.listing import Property, PropertyLocation  # noqa: F401,E402
from app.models.image import PropertyImage, PropertyImageUploadBatch  # noqa: F401,E402
from app.models.promotion import PromotedListing  # noqa: F401,E402
from app.models.bulk_job import BulkJob  # noqa: F401,E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
database_url = os.getenv('DATABASE_PROPERTIES_URL')


if database_url:
    config.set_section_option('alembic', 'sqlalchemy.url', database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata


def include_object(object, name, type_, reflected, compare_to):
    """Keep autogenerate scoped to the tables this service owns.

    PostGIS installs its own tables in this database (spatial_ref_sys, topology
    and the ~40 tiger geocoder tables). They are reflected but absent from
    target_metadata, so autogenerate reads them as "should not exist" and emits
    drop_table for each one — dropping spatial_ref_sys alone breaks every SRID
    4326 lookup in property_locations. Ignoring reflected tables we do not map
    keeps the diff to our own schema.
    """
    if type_ == "table" and reflected and name not in target_metadata.tables:
        return False
    return True


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
