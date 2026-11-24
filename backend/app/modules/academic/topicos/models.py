import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.db_base import Base

NOME_MAX_LENGTH = 200
DESCRICAO_MAX_LENGTH = 1000


class Topico(Base):
    """Tópico de uma unidade curricular (US-019).

    Agrupa as notas de estudo de um assunto ou componente da UC (RN-034). Cada tópico pertence
    a uma única UC (RN-031); a ligação usa ON DELETE RESTRICT, por isso uma UC com tópicos
    não pode ser apagada.
    """

    __tablename__ = "topico"
    __table_args__ = (UniqueConstraint("uc_id", "nome", name="uq_topico_uc_id_nome"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    uc_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("unidade_curricular.id", ondelete="RESTRICT"), index=True
    )
    nome: Mapped[str] = mapped_column(String(NOME_MAX_LENGTH))
    descricao: Mapped[str | None] = mapped_column(String(DESCRICAO_MAX_LENGTH), nullable=True)
    ordem: Mapped[int] = mapped_column(Integer, default=0)
