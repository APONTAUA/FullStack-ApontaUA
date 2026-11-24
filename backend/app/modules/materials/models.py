import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.db_base import Base

TITULO_MAX_LENGTH = 200
DESCRICAO_MAX_LENGTH = 2000
ANO_LETIVO_LENGTH = 9  # «2026/2027»
RESUMO_MAX_LENGTH = 500


class CategoriaMaterial(StrEnum):
    """Categorias de material (RF-019)."""

    APONTAMENTOS = "apontamentos"
    APRESENTACAO = "apresentacao"
    EXERCICIOS = "exercicios"
    EXAME = "exame"
    SOLUCOES = "solucoes"
    OUTRO = "outro"


class OrigemMaterial(StrEnum):
    """Origem do material (RF-027, RN-054)."""

    COMUNIDADE = "comunidade"
    ELEARNING = "elearning"


class EstadoMaterial(StrEnum):
    PUBLICADO = "publicado"
    REMOVIDO = "removido"


def _enum(enum_cls: type[StrEnum], name: str) -> Enum:
    # Guardado como texto, com CHECK, para não depender de tipos ENUM do PostgreSQL.
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=20,
        values_callable=lambda cls: [member.value for member in cls],
    )


class Material(Base):
    """Material académico (US-022).

    Pertence a um tópico e, por ele, a uma unidade curricular (RN-047, RN-031). O autor é o
    identificador interno de quem publicou (RN-048); fica opcional na base de dados para que,
    se a conta for apagada, o material possa ficar sem autoria (RGPD). A ligação à futura
    tabela de utilizadores (EPIC-01) será acrescentada quando essa tabela existir.
    """

    __tablename__ = "material"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    titulo: Mapped[str] = mapped_column(String(TITULO_MAX_LENGTH))
    descricao: Mapped[str | None] = mapped_column(String(DESCRICAO_MAX_LENGTH), nullable=True)
    categoria: Mapped[CategoriaMaterial] = mapped_column(_enum(CategoriaMaterial, "categoria"))
    origem: Mapped[OrigemMaterial] = mapped_column(_enum(OrigemMaterial, "origem"))
    ano_letivo: Mapped[str | None] = mapped_column(String(ANO_LETIVO_LENGTH), nullable=True)
    estado: Mapped[EstadoMaterial] = mapped_column(
        _enum(EstadoMaterial, "estado"), default=EstadoMaterial.PUBLICADO
    )
    topico_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("topico.id", ondelete="RESTRICT"), index=True
    )
    autor_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    publicado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    removido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    versoes: Mapped[list["VersaoMaterial"]] = relationship(
        back_populates="material",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="VersaoMaterial.numero",
    )


class VersaoMaterial(Base):
    """Versão de um material; a publicação cria a versão 1 (modelo de domínio, EPIC-06)."""

    __tablename__ = "versao_material"
    __table_args__ = (
        UniqueConstraint("material_id", "numero", name="uq_versao_material_material_id_numero"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    material_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("material.id", ondelete="CASCADE"), index=True
    )
    numero: Mapped[int] = mapped_column(Integer)
    resumo_alteracao: Mapped[str | None] = mapped_column(String(RESUMO_MAX_LENGTH), nullable=True)
    # O ficheiro original é preservado (RN-055): não pode ser apagado enquanto a versão existir.
    ficheiro_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("stored_file.id", ondelete="RESTRICT"), unique=True
    )
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    material: Mapped[Material] = relationship(back_populates="versoes")
