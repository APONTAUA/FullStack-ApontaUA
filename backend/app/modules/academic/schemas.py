import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from backend.app.modules.academic.models import CODIGO_MAX_LENGTH, NOME_MAX_LENGTH

Codigo = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=CODIGO_MAX_LENGTH)
]
Nome = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=NOME_MAX_LENGTH)
]


class CursoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: Codigo
    nome: Nome


class CursoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: Codigo | None = None
    nome: Nome | None = None


class CursoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo: str
    nome: str


class UnidadeCurricularCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: Codigo
    nome: Nome


class UnidadeCurricularUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: Codigo | None = None
    nome: Nome | None = None


class UnidadeCurricularRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo: str
    nome: str
