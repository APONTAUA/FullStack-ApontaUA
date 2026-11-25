import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.academic.models import (
    AnoLetivo,
    Curso,
    Semestre,
    UnidadeCurricular,
    UnidadeCurricularPeriodo,
)
from backend.app.modules.academic.schemas import (
    AnoLetivoCreate,
    AnoLetivoUpdate,
    CursoCreate,
    CursoUpdate,
    SemestreCreate,
    SemestreUpdate,
    UnidadeCurricularCreate,
    UnidadeCurricularPeriodoCreate,
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


# US-018 — Gestão de anos letivos


class AnoLetivoNaoEncontrado(Exception):
    pass


class AnoLetivoInvalido(Exception):
    pass


class AnoLetivoDuplicado(Exception):
    pass


async def listar_anos_letivos(session: AsyncSession) -> list[AnoLetivo]:
    result = await session.scalars(
        select(AnoLetivo).order_by(AnoLetivo.ano_inicio)
    )
    return list(result)


async def obter_ano_letivo(
    session: AsyncSession,
    ano_id: uuid.UUID,
) -> AnoLetivo:
    ano = await session.get(AnoLetivo, ano_id)

    if ano is None:
        raise AnoLetivoNaoEncontrado

    return ano


async def criar_ano_letivo(
    session: AsyncSession,
    dados: AnoLetivoCreate,
) -> AnoLetivo:
    if dados.ano_fim != dados.ano_inicio + 1:
        raise AnoLetivoInvalido

    ano = AnoLetivo(
        ano_inicio=dados.ano_inicio,
        ano_fim=dados.ano_fim,
    )

    session.add(ano)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise AnoLetivoDuplicado from None

    await session.refresh(ano)
    return ano


async def atualizar_ano_letivo(
    session: AsyncSession,
    ano_id: uuid.UUID,
    dados: AnoLetivoUpdate,
) -> AnoLetivo:
    ano = await obter_ano_letivo(session, ano_id)

    alteracoes = dados.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    novo_inicio = alteracoes.get("ano_inicio", ano.ano_inicio)
    novo_fim = alteracoes.get("ano_fim", ano.ano_fim)

    if novo_fim != novo_inicio + 1:
        raise AnoLetivoInvalido

    ano.ano_inicio = novo_inicio
    ano.ano_fim = novo_fim

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise AnoLetivoDuplicado from None

    await session.refresh(ano)
    return ano


# US-018 — Gestão de semestres


class SemestreNaoEncontrado(Exception):
    pass


class SemestreInvalido(Exception):
    pass


class SemestreDuplicado(Exception):
    pass


async def listar_semestres(
    session: AsyncSession,
    ano_letivo_id: uuid.UUID,
) -> list[Semestre]:
    await obter_ano_letivo(session, ano_letivo_id)

    result = await session.scalars(
        select(Semestre)
        .where(Semestre.ano_letivo_id == ano_letivo_id)
        .order_by(Semestre.numero)
    )
    return list(result)


async def obter_semestre(
    session: AsyncSession,
    semestre_id: uuid.UUID,
) -> Semestre:
    semestre = await session.get(Semestre, semestre_id)

    if semestre is None:
        raise SemestreNaoEncontrado

    return semestre


async def criar_semestre(
    session: AsyncSession,
    dados: SemestreCreate,
) -> Semestre:
    if dados.numero not in (1, 2):
        raise SemestreInvalido

    await obter_ano_letivo(session, dados.ano_letivo_id)

    semestre = Semestre(
        numero=dados.numero,
        ano_letivo_id=dados.ano_letivo_id,
    )

    session.add(semestre)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise SemestreDuplicado from None

    await session.refresh(semestre)
    return semestre


async def atualizar_semestre(
    session: AsyncSession,
    semestre_id: uuid.UUID,
    dados: SemestreUpdate,
) -> Semestre:
    semestre = await obter_semestre(session, semestre_id)

    alteracoes = dados.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    novo_numero = alteracoes.get("numero", semestre.numero)
    novo_ano_id = alteracoes.get("ano_letivo_id", semestre.ano_letivo_id)

    if novo_numero not in (1, 2):
        raise SemestreInvalido

    await obter_ano_letivo(session, novo_ano_id)

    semestre.numero = novo_numero
    semestre.ano_letivo_id = novo_ano_id

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise SemestreDuplicado from None

    await session.refresh(semestre)
    return semestre


# US-018 — Associações entre unidades curriculares e semestres


class AssociacaoPeriodoNaoEncontrada(Exception):
    pass


class AssociacaoPeriodoDuplicada(Exception):
    pass


async def listar_unidades_por_semestre(
    session: AsyncSession,
    semestre_id: uuid.UUID,
) -> list[UnidadeCurricularPeriodo]:
    await obter_semestre(session, semestre_id)

    result = await session.scalars(
        select(UnidadeCurricularPeriodo)
        .where(UnidadeCurricularPeriodo.semestre_id == semestre_id)
        .order_by(UnidadeCurricularPeriodo.unidade_curricular_id)
    )
    return list(result)


async def associar_unidade_periodo(
    session: AsyncSession,
    dados: UnidadeCurricularPeriodoCreate,
) -> UnidadeCurricularPeriodo:
    await obter_unidade_curricular(session, dados.unidade_curricular_id)
    await obter_semestre(session, dados.semestre_id)

    associacao = UnidadeCurricularPeriodo(
        unidade_curricular_id=dados.unidade_curricular_id,
        semestre_id=dados.semestre_id,
    )

    session.add(associacao)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise AssociacaoPeriodoDuplicada from None

    await session.refresh(associacao)
    return associacao


async def remover_associacao_periodo(
    session: AsyncSession,
    associacao_id: uuid.UUID,
) -> None:
    associacao = await session.get(
        UnidadeCurricularPeriodo,
        associacao_id,
    )

    if associacao is None:
        raise AssociacaoPeriodoNaoEncontrada

    await session.delete(associacao)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise AssociacaoPeriodoDuplicada from None

# US-018 — Consulta dos períodos académicos de uma unidade curricular

async def listar_periodos_unidade_curricular(
    session: AsyncSession,
    unidade_id: uuid.UUID,
) -> list[tuple[UnidadeCurricularPeriodo, Semestre, AnoLetivo]]:
    await obter_unidade_curricular(session, unidade_id)

    consulta = (
        select(UnidadeCurricularPeriodo, Semestre, AnoLetivo)
        .join(Semestre, UnidadeCurricularPeriodo.semestre_id == Semestre.id)
        .join(AnoLetivo, Semestre.ano_letivo_id == AnoLetivo.id)
        .where(UnidadeCurricularPeriodo.unidade_curricular_id == unidade_id)
        .order_by(AnoLetivo.ano_inicio, Semestre.numero)
    )

    resultado = await session.execute(consulta)
    return [
        (associacao, semestre, ano)
        for associacao, semestre, ano in resultado.all()
    ]
