import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from backend.app.core.database import database_url
from backend.app.core.db_base import Base
from backend.app.modules.academic import models as academic_models  # noqa: F401
from backend.app.modules.academic.topicos import models as topico_models  # noqa: F401
from backend.app.modules.materials import models as materials_models  # noqa: F401
from backend.app.modules.storage import models as storage_models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Cada módulo com tabelas deve ser importado acima para entrar no autogenerate.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Gera o SQL sem ligar à base de dados (`alembic upgrade head --sql`)."""
    context.configure(
        url=database_url.render_as_string(hide_password=True),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = create_async_engine(database_url, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
