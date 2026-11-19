import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.db_base import Base

CODIGO_MAX_LENGTH = 20
NOME_MAX_LENGTH = 200


class Curso(Base):
    """Curso da UA (RF-016, US-015). As unidades curriculares ligam-se a ele (US-017)."""

    __tablename__ = "curso"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(CODIGO_MAX_LENGTH), unique=True)
    nome: Mapped[str] = mapped_column(String(NOME_MAX_LENGTH))
    unidades_curriculares: Mapped[list["UnidadeCurricular"]] = relationship(back_populates="curso")


class UnidadeCurricular(Base):
    """Unidade curricular da UA (RF-016, RF-017, US-016)."""

    __tablename__ = "unidade_curricular"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(CODIGO_MAX_LENGTH), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(NOME_MAX_LENGTH), nullable=False)

    curso_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("curso.id", ondelete="RESTRICT"),
        nullable=True,
    )

    curso: Mapped["Curso | None"] = relationship(back_populates="unidades_curriculares")


class AnoLetivo(Base):
    """Ano letivo da UA (US-018)."""

    __tablename__ = "ano_letivo"
    __table_args__ = (
        CheckConstraint(
            "ano_fim = ano_inicio + 1",
            name="anos_consecutivos",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ano_inicio: Mapped[int] = mapped_column(nullable=False, unique=True)
    ano_fim: Mapped[int] = mapped_column(nullable=False)


class Semestre(Base):
    """Semestre de um ano letivo (US-018)."""

    __tablename__ = "semestre"

    __table_args__ = (
        UniqueConstraint(
            "ano_letivo_id",
            "numero",
            name="uq_semestre_ano_letivo_numero",
        ),
        CheckConstraint(
            "numero IN (1, 2)",
            name="numero_valido",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    numero: Mapped[int] = mapped_column(nullable=False)

    ano_letivo_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("ano_letivo.id", ondelete="RESTRICT"),
        nullable=False,
    )


class UnidadeCurricularPeriodo(Base):
    """Associação de uma unidade curricular a um período académico (US-018)."""

    __tablename__ = "unidade_curricular_periodo"

    __table_args__ = (
        UniqueConstraint(
            "unidade_curricular_id",
            "semestre_id",
            name="uq_unidade_curricular_periodo",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    unidade_curricular_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("unidade_curricular.id", ondelete="RESTRICT"),
        nullable=False,
    )

    semestre_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("semestre.id", ondelete="RESTRICT"),
        nullable=False,
    )
