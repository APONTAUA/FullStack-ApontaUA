import re
import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from backend.app.modules.materials.models import (
    DESCRICAO_MAX_LENGTH,
    TITULO_MAX_LENGTH,
    CategoriaMaterial,
    EstadoMaterial,
    OrigemMaterial,
)

Titulo = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TITULO_MAX_LENGTH)
]
Descricao = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=DESCRICAO_MAX_LENGTH)
]
ANO_LETIVO = re.compile(r"^(\d{4})/(\d{4})$")


class MaterialCreate(BaseModel):
    """Metadados enviados com o ficheiro (formulário multipart)."""

    model_config = ConfigDict(extra="forbid")

    titulo: Titulo
    descricao: Descricao | None = None
    categoria: CategoriaMaterial
    uc_id: uuid.UUID
    topico_id: uuid.UUID
    ano_letivo: str | None = None

    @field_validator("descricao")
    @classmethod
    def descricao_vazia_fica_nula(cls, value: str | None) -> str | None:
        return value or None

    @field_validator("ano_letivo")
    @classmethod
    def ano_letivo_valido(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        match = ANO_LETIVO.match(value.strip())
        if not match or int(match.group(2)) != int(match.group(1)) + 1:
            raise ValueError("Use the format YYYY/YYYY with consecutive years, e.g. 2026/2027.")
        return match.group(0)


class FicheiroRead(BaseModel):
    nome_original: str
    tipo: str
    tamanho_bytes: int
    sha256: str


class VersaoRead(BaseModel):
    numero: int
    criada_em: datetime
    ficheiro: FicheiroRead


class MaterialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    titulo: str
    descricao: str | None
    categoria: CategoriaMaterial
    origem: OrigemMaterial
    ano_letivo: str | None
    estado: EstadoMaterial
    uc_id: uuid.UUID
    topico_id: uuid.UUID
    autor_id: uuid.UUID | None
    publicado_em: datetime
    versao_atual: VersaoRead
