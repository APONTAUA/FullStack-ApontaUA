import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db_session
from backend.app.core.permissions import CurrentRole, Papel, require_roles
from backend.app.modules.academic import service
from backend.app.modules.academic.schemas import (
    CursoCreate,
    CursoRead,
    CursoUpdate,
    UnidadeCurricularCreate,
    UnidadeCurricularRead,
    UnidadeCurricularUpdate,
)

router = APIRouter(prefix="/cursos")
unidades_router = APIRouter(prefix="/unidades-curriculares")


Session = Annotated[AsyncSession, Depends(get_db_session)]
# RN-035: só utilizadores com permissões adequadas gerem a estrutura académica.
GestorEstrutura = Depends(require_roles(Papel.ADMINISTRADOR))

NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Degree programme not found."
)
DUPLICATE = HTTPException(
    status_code=status.HTTP_409_CONFLICT, detail="A degree programme with this code already exists."
)


@router.get("", response_model=list[CursoRead], summary="Lista os cursos")
async def listar(session: Session, _: CurrentRole) -> list[CursoRead]:
    return [CursoRead.model_validate(c) for c in await service.listar_cursos(session)]


@router.get("/{curso_id}", response_model=CursoRead, summary="Mostra um curso")
async def obter(curso_id: uuid.UUID, session: Session, _: CurrentRole) -> CursoRead:
    try:
        return CursoRead.model_validate(await service.obter_curso(session, curso_id))
    except service.CursoNaoEncontrado:
        raise NOT_FOUND from None


@router.post(
    "",
    response_model=CursoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GestorEstrutura],
    summary="Cria um curso",
)
async def criar(dados: CursoCreate, session: Session) -> CursoRead:
    try:
        return CursoRead.model_validate(await service.criar_curso(session, dados))
    except service.CodigoDuplicado:
        raise DUPLICATE from None


@router.patch(
    "/{curso_id}",
    response_model=CursoRead,
    dependencies=[GestorEstrutura],
    summary="Atualiza um curso",
)
async def atualizar(curso_id: uuid.UUID, dados: CursoUpdate, session: Session) -> CursoRead:
    try:
        return CursoRead.model_validate(await service.atualizar_curso(session, curso_id, dados))
    except service.CursoNaoEncontrado:
        raise NOT_FOUND from None
    except service.CodigoDuplicado:
        raise DUPLICATE from None


@router.delete(
    "/{curso_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[GestorEstrutura],
    summary="Remove um curso sem associações",
)
async def remover(curso_id: uuid.UUID, session: Session) -> Response:
    try:
        await service.remover_curso(session, curso_id)
    except service.CursoNaoEncontrado:
        raise NOT_FOUND from None
    except service.CursoComAssociacoes:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The degree programme still has associated course units.",
        ) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Endpoints de unidades curriculares (US-016, #95)

UC_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Course unit not found.",
)
UC_DUPLICATE = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="A course unit with this code already exists.",
)


@unidades_router.get(
    "",
    response_model=list[UnidadeCurricularRead],
    summary="Lista as unidades curriculares",
)
async def listar_unidades(
    session: Session,
    _: CurrentRole,
) -> list[UnidadeCurricularRead]:
    unidades = await service.listar_unidades_curriculares(session)
    return [UnidadeCurricularRead.model_validate(uc) for uc in unidades]


@unidades_router.get(
    "/{unidade_id}",
    response_model=UnidadeCurricularRead,
    summary="Mostra uma unidade curricular",
)
async def obter_unidade(
    unidade_id: uuid.UUID,
    session: Session,
    _: CurrentRole,
) -> UnidadeCurricularRead:
    try:
        unidade = await service.obter_unidade_curricular(session, unidade_id)
        return UnidadeCurricularRead.model_validate(unidade)
    except service.UnidadeCurricularNaoEncontrada:
        raise UC_NOT_FOUND from None


@unidades_router.post(
    "",
    response_model=UnidadeCurricularRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GestorEstrutura],
    summary="Cria uma unidade curricular",
)
async def criar_unidade(
    dados: UnidadeCurricularCreate,
    session: Session,
) -> UnidadeCurricularRead:
    try:
        unidade = await service.criar_unidade_curricular(session, dados)
        return UnidadeCurricularRead.model_validate(unidade)
    except service.CodigoDuplicado:
        raise UC_DUPLICATE from None


@unidades_router.patch(
    "/{unidade_id}",
    response_model=UnidadeCurricularRead,
    dependencies=[GestorEstrutura],
    summary="Atualiza uma unidade curricular",
)
async def atualizar_unidade(
    unidade_id: uuid.UUID,
    dados: UnidadeCurricularUpdate,
    session: Session,
) -> UnidadeCurricularRead:
    try:
        unidade = await service.atualizar_unidade_curricular(session, unidade_id, dados)
        return UnidadeCurricularRead.model_validate(unidade)
    except service.UnidadeCurricularNaoEncontrada:
        raise UC_NOT_FOUND from None
    except service.CodigoDuplicado:
        raise UC_DUPLICATE from None


@unidades_router.delete(
    "/{unidade_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[GestorEstrutura],
    summary="Remove uma unidade curricular sem associações",
)
async def remover_unidade(
    unidade_id: uuid.UUID,
    session: Session,
) -> Response:
    try:
        await service.remover_unidade_curricular(session, unidade_id)
    except service.UnidadeCurricularNaoEncontrada:
        raise UC_NOT_FOUND from None
    except service.UnidadeCurricularComAssociacoes:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The course unit still has academic associations.",
        ) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
