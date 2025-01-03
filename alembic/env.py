from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# This is the Alembic Config object, which
# provides access to values within the .ini file
config = context.config


# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -------------------------------------------------------
# Import your Base (and models) so Alembic sees them
# -------------------------------------------------------
# e.g. app.database.Base or app.models.Base
from app.database import Base, settings
# Import all your models so they get attached to Base.metadata
import app.models  # or from app import models

# For “autogenerate” support, give Alembic a metadata target:
target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URI)


def run_migrations_offline():
    """
    Run migrations in 'offline' mode.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """
    Run migrations in 'online' mode.
    """
    # Create an Engine and associate a connection with the context.
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
