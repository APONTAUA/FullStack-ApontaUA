from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Nomes estáveis para restrições, para que as migrações Alembic sejam previsíveis.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base comum a todos os modelos persistidos dos módulos."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
