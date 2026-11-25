import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db_session
from backend.app.core.permissions import CurrentRole, Papel, require_roles
from backend.app.modules.academic import service
from backend.app.modules.academic.schemas import (
    AnoLetivoCreate,
    AnoLetivoRead,
    AnoLetivoUpdate,
    CursoCreate,
    CursoRead,
    CursoUpdate,
    SemestreCreate,
    SemestreRead,
    SemestreUpdate,
    UnidadeCurricularCreate,
    UnidadeCurricularPeriodoCreate,
    UnidadeCurricularPeriodoDetalheRead,
    UnidadeCurricularPeriodoRead,
    UnidadeCurricularRead,
    UnidadeCurricularUpdate,
)

router = APIRouter(prefix="/cursos")
unidades_router = APIRouter(prefix="/unidades-curriculares")
anos_letivos_router = APIRouter(prefix="/anos-letivos")
semestres_router = APIRouter(prefix="/semestres")


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

    except service.CursoNaoEncontrado:
        raise NOT_FOUND from None


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

    except service.CursoNaoEncontrado:
        raise NOT_FOUND from None


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

# US-018 — Endpoints de anos letivos


@anos_letivos_router.get(
    "",
    response_model=list[AnoLetivoRead],
    summary="Lista os anos letivos",
)
async def listar_anos_letivos(
    session: Session,
    _: CurrentRole,
) -> list[AnoLetivoRead]:
    anos = await service.listar_anos_letivos(session)
    return [AnoLetivoRead.model_validate(ano) for ano in anos]


@anos_letivos_router.get(
    "/{ano_id}",
    response_model=AnoLetivoRead,
    summary="Mostra um ano letivo",
)
async def obter_ano_letivo(
    ano_id: uuid.UUID,
    session: Session,
    _: CurrentRole,
) -> AnoLetivoRead:
    try:
        ano = await service.obter_ano_letivo(session, ano_id)
        return AnoLetivoRead.model_validate(ano)
    except service.AnoLetivoNaoEncontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found.",
        ) from None


@anos_letivos_router.post(
    "",
    response_model=AnoLetivoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GestorEstrutura],
    summary="Cria um ano letivo",
)
async def criar_ano_letivo(
    dados: AnoLetivoCreate,
    session: Session,
) -> AnoLetivoRead:
    try:
        ano = await service.criar_ano_letivo(session, dados)
        return AnoLetivoRead.model_validate(ano)
    except service.AnoLetivoInvalido:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The academic year must contain consecutive years.",
        ) from None
    except service.AnoLetivoDuplicado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Academic year already exists.",
        ) from None


@anos_letivos_router.patch(
    "/{ano_id}",
    response_model=AnoLetivoRead,
    dependencies=[GestorEstrutura],
    summary="Atualiza um ano letivo",
)
async def atualizar_ano_letivo(
    ano_id: uuid.UUID,
    dados: AnoLetivoUpdate,
    session: Session,
) -> AnoLetivoRead:
    try:
        ano = await service.atualizar_ano_letivo(
            session,
            ano_id,
            dados,
        )
        return AnoLetivoRead.model_validate(ano)
    except service.AnoLetivoNaoEncontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found.",
        ) from None
    except service.AnoLetivoInvalido:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The academic year must contain consecutive years.",
        ) from None
    except service.AnoLetivoDuplicado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Academic year already exists.",
        ) from None


# US-018 — Endpoints de semestres


@semestres_router.get(
    "/{semestre_id}",
    response_model=SemestreRead,
    summary="Mostra um semestre",
)
async def obter_semestre(
    semestre_id: uuid.UUID,
    session: Session,
    _: CurrentRole,
) -> SemestreRead:
    try:
        semestre = await service.obter_semestre(session, semestre_id)
        return SemestreRead.model_validate(semestre)
    except service.SemestreNaoEncontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Semester not found.",
        ) from None


@semestres_router.post(
    "",
    response_model=SemestreRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GestorEstrutura],
    summary="Cria um semestre",
)
async def criar_semestre(
    dados: SemestreCreate,
    session: Session,
) -> SemestreRead:
    try:
        semestre = await service.criar_semestre(session, dados)
        return SemestreRead.model_validate(semestre)
    except service.AnoLetivoNaoEncontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found.",
        ) from None
    except service.SemestreInvalido:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Semester number must be 1 or 2.",
        ) from None
    except service.SemestreDuplicado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Semester already exists.",
        ) from None


@semestres_router.patch(
    "/{semestre_id}",
    response_model=SemestreRead,
    dependencies=[GestorEstrutura],
    summary="Atualiza um semestre",
)
async def atualizar_semestre(
    semestre_id: uuid.UUID,
    dados: SemestreUpdate,
    session: Session,
) -> SemestreRead:
    try:
        semestre = await service.atualizar_semestre(
            session,
            semestre_id,
            dados,
        )
        return SemestreRead.model_validate(semestre)
    except service.SemestreNaoEncontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Semester not found.",
        ) from None
    except service.AnoLetivoNaoEncontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found.",
        ) from None
    except service.SemestreInvalido:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Semester number must be 1 or 2.",
        ) from None
    except service.SemestreDuplicado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Semester already exists.",
        ) from None


@anos_letivos_router.get(
    "/{ano_id}/semestres",
    response_model=list[SemestreRead],
    summary="Lista os semestres de um ano letivo",
)
async def listar_semestres_ano_letivo(
    ano_id: uuid.UUID,
    session: Session,
    _: CurrentRole,
) -> list[SemestreRead]:
    try:
        semestres = await service.listar_semestres(session, ano_id)
        return [SemestreRead.model_validate(s) for s in semestres]
    except service.AnoLetivoNaoEncontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found.",
        ) from None

# US-018 — Associações de unidades curriculares a semestres


@semestres_router.get(
    "/{semestre_id}/unidades-curriculares",
    response_model=list[UnidadeCurricularPeriodoRead],
    summary="Lista as unidades curriculares de um semestre",
)
async def listar_unidades_semestre(
    semestre_id: uuid.UUID,
    session: Session,
    _: CurrentRole,
) -> list[UnidadeCurricularPeriodoRead]:
    try:
        associacoes = await service.listar_unidades_por_semestre(
            session, semestre_id
        )
        return [
            UnidadeCurricularPeriodoRead.model_validate(a)
            for a in associacoes
        ]
    except service.SemestreNaoEncontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Semester not found.",
        ) from None


@semestres_router.post(
    "/{semestre_id}/unidades-curriculares",
    response_model=UnidadeCurricularPeriodoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GestorEstrutura],
    summary="Associa uma unidade curricular a um semestre",
)
async def associar_unidade_semestre(
    semestre_id: uuid.UUID,
    dados: UnidadeCurricularPeriodoCreate,
    session: Session,
) -> UnidadeCurricularPeriodoRead:
    if dados.semestre_id != semestre_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Semester ID does not match the URL.",
        )

    try:
        associacao = await service.associar_unidade_periodo(
            session, dados
        )
        return UnidadeCurricularPeriodoRead.model_validate(associacao)
    except service.SemestreNaoEncontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Semester not found.",
        ) from None
    except service.UnidadeCurricularNaoEncontrada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course unit not found.",
        ) from None
    except service.AssociacaoPeriodoDuplicada:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Course unit is already associated with this semester.",
        ) from None


@semestres_router.delete(
    "/associacoes/{associacao_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[GestorEstrutura],
    summary="Remove uma associação académica",
)
async def remover_unidade_semestre(
    associacao_id: uuid.UUID,
    session: Session,
) -> Response:
    try:
        await service.remover_associacao_periodo(session, associacao_id)
    except service.AssociacaoPeriodoNaoEncontrada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic association not found.",
        ) from None

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# US-018 — Consulta dos períodos académicos de uma unidade curricular


@unidades_router.get(
    "/{unidade_id}/periodos",
    response_model=list[UnidadeCurricularPeriodoDetalheRead],
    summary="Lista os períodos académicos de uma unidade curricular",
)
async def listar_periodos_unidade(
    unidade_id: uuid.UUID,
    session: Session,
    _: CurrentRole,
) -> list[UnidadeCurricularPeriodoDetalheRead]:
    try:
        periodos = await service.listar_periodos_unidade_curricular(
            session, unidade_id
        )
    except service.UnidadeCurricularNaoEncontrada:
        raise UC_NOT_FOUND from None

    return [
        UnidadeCurricularPeriodoDetalheRead(
            id=associacao.id,
            unidade_curricular_id=associacao.unidade_curricular_id,
            semestre_id=semestre.id,
            numero_semestre=semestre.numero,
            ano_letivo_id=ano.id,
            ano_inicio=ano.ano_inicio,
            ano_fim=ano.ano_fim,
        )
        for associacao, semestre, ano in periodos
    ]
