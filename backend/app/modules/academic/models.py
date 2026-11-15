import uuid

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.db_base import Base

CODIGO_MAX_LENGTH = 20
NOME_MAX_LENGTH = 200


class Curso(Base):
    """Curso da UA (RF-016, US-015). As unidades curriculares ligam-se a ele (US-017)."""

    __tablename__ = "curso"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(CODIGO_MAX_LENGTH), unique=True)
    nome: Mapped[str] = mapped_column(String(NOME_MAX_LENGTH))
