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

    codigo: Codigo = None
    nome: Nome = None


class UnidadeCurricularRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo: str
    nome: str

# US-018 — Gestão de anos letivos e semestres


class AnoLetivoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ano_inicio: int
    ano_fim: int


class AnoLetivoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ano_inicio: int | None = None
    ano_fim: int | None = None


class AnoLetivoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ano_inicio: int
    ano_fim: int


class SemestreCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    numero: int
    ano_letivo_id: uuid.UUID


class SemestreUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    numero: int | None = None
    ano_letivo_id: uuid.UUID | None = None


class SemestreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    numero: int
    ano_letivo_id: uuid.UUID


class UnidadeCurricularPeriodoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    unidade_curricular_id: uuid.UUID
    semestre_id: uuid.UUID


class UnidadeCurricularPeriodoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    unidade_curricular_id: uuid.UUID
    semestre_id: uuid.UUID


# US-018 — Detalhes do período académico de uma unidade curricular

class UnidadeCurricularPeriodoDetalheRead(BaseModel):
    id: uuid.UUID
    unidade_curricular_id: uuid.UUID
    semestre_id: uuid.UUID
    numero_semestre: int
    ano_letivo_id: uuid.UUID
    ano_inicio: int
    ano_fim: int
