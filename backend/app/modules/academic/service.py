import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.academic.models import Curso, UnidadeCurricular
from backend.app.modules.academic.schemas import (
    CursoCreate,
    CursoUpdate,
    UnidadeCurricularCreate,
    UnidadeCurricularUpdate,
)


class CursoNaoEncontrado(Exception):
    pass


class CodigoDuplicado(Exception):
    pass


class CursoComAssociacoes(Exception):
    pass


async def listar_cursos(session: AsyncSession) -> list[Curso]:
    result = await session.scalars(select(Curso).order_by(Curso.nome, Curso.codigo))
    return list(result)


async def obter_curso(session: AsyncSession, curso_id: uuid.UUID) -> Curso:
    curso = await session.get(Curso, curso_id)
    if curso is None:
        raise CursoNaoEncontrado
    return curso


async def _codigo_em_uso(
    session: AsyncSession, codigo: str, ignorar_id: uuid.UUID | None = None
) -> bool:
    query = select(Curso.id).where(Curso.codigo == codigo)
    if ignorar_id is not None:
        query = query.where(Curso.id != ignorar_id)
    return await session.scalar(query) is not None


async def criar_curso(session: AsyncSession, dados: CursoCreate) -> Curso:
    if await _codigo_em_uso(session, dados.codigo):
        raise CodigoDuplicado
    curso = Curso(codigo=dados.codigo, nome=dados.nome)
    session.add(curso)
    try:
        await session.commit()
    except IntegrityError:
        # Dois pedidos em simultâneo com o mesmo código: a restrição única decide.
        await session.rollback()
        raise CodigoDuplicado from None
    await session.refresh(curso)
    return curso


async def atualizar_curso(session: AsyncSession, curso_id: uuid.UUID, dados: CursoUpdate) -> Curso:
    curso = await obter_curso(session, curso_id)
    alteracoes = dados.model_dump(exclude_unset=True, exclude_none=True)
    novo_codigo = alteracoes.get("codigo")
    if novo_codigo is not None and await _codigo_em_uso(session, novo_codigo, curso_id):
        raise CodigoDuplicado
    for campo, valor in alteracoes.items():
        setattr(curso, campo, valor)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise CodigoDuplicado from None
    await session.refresh(curso)
    return curso


async def remover_curso(session: AsyncSession, curso_id: uuid.UUID) -> None:
    curso = await obter_curso(session, curso_id)
    await session.delete(curso)
    try:
        await session.commit()
    except IntegrityError:
        # As ligações a unidades curriculares (US-017) usam ON DELETE RESTRICT,
        # por isso um curso com associações não pode ser apagado (US-015, critério 4).
        await session.rollback()
        raise CursoComAssociacoes from None


async def listar_unidades_curriculares(session: AsyncSession) -> list[UnidadeCurricular]:
    result = await session.scalars(
        select(UnidadeCurricular).order_by(
            UnidadeCurricular.nome,
            UnidadeCurricular.codigo,
        )
    )
    return list(result)


class UnidadeCurricularNaoEncontrada(Exception):
    pass


async def obter_unidade_curricular(
    session: AsyncSession, unidade_id: uuid.UUID
) -> UnidadeCurricular:
    unidade = await session.get(UnidadeCurricular, unidade_id)

    if unidade is None:
        raise UnidadeCurricularNaoEncontrada

    return unidade


async def _codigo_unidade_em_uso(
    session: AsyncSession,
    codigo: str,
    ignorar_id: uuid.UUID | None = None,
) -> bool:
    query = select(UnidadeCurricular.id).where(UnidadeCurricular.codigo == codigo)

    if ignorar_id is not None:
        query = query.where(UnidadeCurricular.id != ignorar_id)

    return await session.scalar(query) is not None


async def criar_unidade_curricular(
    session: AsyncSession,
    dados: UnidadeCurricularCreate,
) -> UnidadeCurricular:
    if await _codigo_unidade_em_uso(session, dados.codigo):
        raise CodigoDuplicado

    if dados.curso_id is not None:
        await obter_curso(session, dados.curso_id)

    unidade = UnidadeCurricular(
        codigo=dados.codigo,
        nome=dados.nome,
        curso_id=dados.curso_id,
    )

    session.add(unidade)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise CodigoDuplicado from None

    await session.refresh(unidade)

    return unidade


async def atualizar_unidade_curricular(
    session: AsyncSession,
    unidade_id: uuid.UUID,
    dados: UnidadeCurricularUpdate,
) -> UnidadeCurricular:
    unidade = await obter_unidade_curricular(session, unidade_id)

    alteracoes = dados.model_dump(exclude_unset=True)

    alteracoes = {
        campo: valor
        for campo, valor in alteracoes.items()
        if campo == "curso_id" or valor is not None
    }

    # Verifica se o novo curso existe.
    if alteracoes.get("curso_id") is not None:
        await obter_curso(session, alteracoes["curso_id"])

    novo_codigo = alteracoes.get("codigo")

    if novo_codigo is not None and await _codigo_unidade_em_uso(session, novo_codigo, unidade_id):
        raise CodigoDuplicado

    for campo, valor in alteracoes.items():
        setattr(unidade, campo, valor)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise CodigoDuplicado from None

    await session.refresh(unidade)

    return unidade


class UnidadeCurricularComAssociacoes(Exception):
    pass


async def remover_unidade_curricular(
    session: AsyncSession,
    unidade_id: uuid.UUID,
) -> None:
    unidade = await obter_unidade_curricular(session, unidade_id)

    await session.delete(unidade)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise UnidadeCurricularComAssociacoes from None
