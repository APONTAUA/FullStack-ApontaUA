import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from backend.app.modules.academic.topicos.models import DESCRICAO_MAX_LENGTH, NOME_MAX_LENGTH

Nome = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=NOME_MAX_LENGTH)
]
Descricao = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=DESCRICAO_MAX_LENGTH)
]


def _vazio_para_none(value: str | None) -> str | None:
    return value or None


class TopicoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: Nome
    descricao: Descricao | None = None

    _descricao = field_validator("descricao")(_vazio_para_none)


class TopicoUpdate(BaseModel):
    """A UC de um tópico não pode ser alterada, para não mudar a UC das suas notas (RN-036)."""

    model_config = ConfigDict(extra="forbid")

    nome: Nome | None = None
    descricao: Descricao | None = None

    _descricao = field_validator("descricao")(_vazio_para_none)


class TopicoOrdem(BaseModel):
    """Nova ordem dos tópicos de uma UC: todos os tópicos da UC, sem repetições."""

    model_config = ConfigDict(extra="forbid")

    topico_ids: list[uuid.UUID] = Field(min_length=1)


class TopicoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    uc_id: uuid.UUID
    nome: str
    descricao: str | None
    ordem: int
