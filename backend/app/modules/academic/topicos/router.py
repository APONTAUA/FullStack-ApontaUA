import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db_session
from backend.app.core.permissions import CurrentRole, Papel, require_roles
from backend.app.modules.academic.topicos import service
from backend.app.modules.academic.topicos.schemas import (
    TopicoCreate,
    TopicoOrdem,
    TopicoRead,
    TopicoUpdate,
)

router = APIRouter()

Session = Annotated[AsyncSession, Depends(get_db_session)]
# Critério 8 e RN-035: só utilizadores com permissões adequadas gerem a estrutura académica.
GestorEstrutura = Depends(require_roles(Papel.ADMINISTRADOR))

UC_NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course unit not found.")
TOPIC_NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found.")
DUPLICATE = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="A topic with this name already exists in this course unit.",
)


@router.get(
    "/unidades-curriculares/{uc_id}/topicos",
    response_model=list[TopicoRead],
    summary="Lista os tópicos de uma unidade curricular",
)
async def listar(uc_id: uuid.UUID, session: Session, _: CurrentRole) -> list[TopicoRead]:
    try:
        topicos = await service.listar_topicos(session, uc_id)
    except service.UnidadeCurricularNaoEncontrada:
        raise UC_NOT_FOUND from None
    return [TopicoRead.model_validate(t) for t in topicos]


@router.post(
    "/unidades-curriculares/{uc_id}/topicos",
    response_model=TopicoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GestorEstrutura],
    summary="Cria um tópico numa unidade curricular",
)
async def criar(uc_id: uuid.UUID, dados: TopicoCreate, session: Session) -> TopicoRead:
    try:
        return TopicoRead.model_validate(await service.criar_topico(session, uc_id, dados))
    except service.UnidadeCurricularNaoEncontrada:
        raise UC_NOT_FOUND from None
    except service.NomeDuplicado:
        raise DUPLICATE from None


@router.put(
    "/unidades-curriculares/{uc_id}/topicos/ordem",
    response_model=list[TopicoRead],
    dependencies=[GestorEstrutura],
    summary="Reordena os tópicos de uma unidade curricular",
)
async def reordenar(uc_id: uuid.UUID, dados: TopicoOrdem, session: Session) -> list[TopicoRead]:
    try:
        topicos = await service.reordenar_topicos(session, uc_id, dados.topico_ids)
    except service.UnidadeCurricularNaoEncontrada:
        raise UC_NOT_FOUND from None
    except service.OrdemInvalida:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The list must contain every topic of the course unit exactly once.",
        ) from None
    return [TopicoRead.model_validate(t) for t in topicos]


@router.get("/topicos/{topico_id}", response_model=TopicoRead, summary="Mostra um tópico")
async def obter(topico_id: uuid.UUID, session: Session, _: CurrentRole) -> TopicoRead:
    try:
        return TopicoRead.model_validate(await service.obter_topico(session, topico_id))
    except service.TopicoNaoEncontrado:
        raise TOPIC_NOT_FOUND from None


@router.patch(
    "/topicos/{topico_id}",
    response_model=TopicoRead,
    dependencies=[GestorEstrutura],
    summary="Atualiza um tópico",
)
async def atualizar(topico_id: uuid.UUID, dados: TopicoUpdate, session: Session) -> TopicoRead:
    try:
        return TopicoRead.model_validate(await service.atualizar_topico(session, topico_id, dados))
    except service.TopicoNaoEncontrado:
        raise TOPIC_NOT_FOUND from None
    except service.NomeDuplicado:
        raise DUPLICATE from None


@router.delete(
    "/topicos/{topico_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[GestorEstrutura],
    summary="Remove um tópico sem notas de estudo",
)
async def remover(topico_id: uuid.UUID, session: Session) -> Response:
    try:
        await service.remover_topico(session, topico_id)
    except service.TopicoNaoEncontrado:
        raise TOPIC_NOT_FOUND from None
    except service.TopicoComNotas:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The topic still has associated study notes.",
        ) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
