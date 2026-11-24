from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db_session
from backend.app.core.permissions import CurrentUserId, Papel, require_roles
from backend.app.modules.materials import service
from backend.app.modules.materials.formats import TIPOS_POR_EXTENSAO
from backend.app.modules.materials.schemas import (
    FicheiroRead,
    MaterialCreate,
    MaterialRead,
    VersaoRead,
)
from backend.app.modules.storage.service import ObjectStorage

router = APIRouter(prefix="/materiais")

Session = Annotated[AsyncSession, Depends(get_db_session)]

# Critério 1: utilizadores com permissão de publicar. Enquanto não há gestão de papéis (EPIC-02),
# todos os papéis podem publicar; não há papel de curador nem aprovação prévia (RN-023, US-008).
PODE_PUBLICAR = Depends(require_roles(*Papel))


def get_armazenamento() -> service.Armazenamento:
    try:
        return ObjectStorage()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File storage is not configured.",
        ) from None


Armazenamento = Annotated[service.Armazenamento, Depends(get_armazenamento)]


class PublicacaoForm(MaterialCreate):
    """Formulário multipart: os metadados do material e o ficheiro original."""

    ficheiro: Annotated[UploadFile, File(description="Ficheiro original do material")]


FORMATOS = ", ".join(sorted(ext.lstrip(".") for ext in TIPOS_POR_EXTENSAO))
ERROS = {
    service.UnidadeCurricularNaoEncontrada: (status.HTTP_404_NOT_FOUND, "Course unit not found."),
    service.TopicoNaoEncontrado: (status.HTTP_404_NOT_FOUND, "Topic not found."),
    service.AnoLetivoNaoEncontrado: (
        status.HTTP_404_NOT_FOUND,
        "Academic year not found.",
    ),
    service.TopicoForaDaUnidadeCurricular: (
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "The topic does not belong to the selected course unit.",
    ),
    service.FormatoNaoSuportado: (
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Unsupported file format. Accepted formats: {FORMATOS}.",
    ),
    service.FicheiroVazio: (status.HTTP_422_UNPROCESSABLE_CONTENT, "The file is empty."),
    service.FicheiroDemasiadoGrande: (
        status.HTTP_413_CONTENT_TOO_LARGE,
        f"The file exceeds the maximum size of {settings.max_upload_size_mb} MB.",
    ),
}


@router.post(
    "",
    response_model=MaterialRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[PODE_PUBLICAR],
    summary="Publica um material da comunidade",
)
async def publicar(
    formulario: Annotated[PublicacaoForm, Form(media_type="multipart/form-data")],
    autor_id: CurrentUserId,
    session: Session,
    armazenamento: Armazenamento,
) -> MaterialRead:
    try:
        publicacao = await service.publicar_material(
            session,
            armazenamento,
            MaterialCreate.model_validate(formulario.model_dump(exclude={"ficheiro"})),
            autor_id,
            formulario.ficheiro,
            max_bytes=settings.max_upload_size_mb * 1024 * 1024,
        )
    except tuple(ERROS) as erro:
        codigo, mensagem = ERROS[type(erro)]
        raise HTTPException(status_code=codigo, detail=mensagem) from None

    material, versao, guardado = publicacao.material, publicacao.versao, publicacao.ficheiro
    return MaterialRead(
        id=material.id,
        titulo=material.titulo,
        descricao=material.descricao,
        categoria=material.categoria,
        origem=material.origem,
        ano_letivo=material.ano_letivo,
        estado=material.estado,
        uc_id=publicacao.uc_id,
        topico_id=material.topico_id,
        autor_id=material.autor_id,
        publicado_em=material.publicado_em,
        versao_atual=VersaoRead(
            numero=versao.numero,
            criada_em=versao.criada_em,
            ficheiro=FicheiroRead(
                nome_original=guardado.original_name,
                tipo=guardado.mime_type,
                tamanho_bytes=guardado.size_bytes,
                sha256=guardado.checksum_sha256,
            ),
        ),
    )
