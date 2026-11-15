import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db_session
from backend.app.core.permissions import CurrentRole, Papel, require_roles
from backend.app.modules.academic import service
from backend.app.modules.academic.schemas import CursoCreate, CursoRead, CursoUpdate

router = APIRouter(prefix="/cursos")

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
