import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.academic.models import UnidadeCurricular
from backend.app.modules.academic.topicos.models import Topico
from backend.app.modules.academic.topicos.schemas import TopicoCreate, TopicoUpdate


class UnidadeCurricularNaoEncontrada(Exception):
    pass


class TopicoNaoEncontrado(Exception):
    pass


class NomeDuplicado(Exception):
    pass


class OrdemInvalida(Exception):
    pass


class TopicoComNotas(Exception):
    pass


async def _garantir_uc(session: AsyncSession, uc_id: uuid.UUID) -> None:
    # Critérios 5 e 6: um tópico só pode pertencer a uma UC existente.
    if await session.get(UnidadeCurricular, uc_id) is None:
        raise UnidadeCurricularNaoEncontrada


async def _nome_em_uso(
    session: AsyncSession, uc_id: uuid.UUID, nome: str, ignorar_id: uuid.UUID | None = None
) -> bool:
    # Na mesma UC, «Integrais» e «integrais» contam como o mesmo tópico.
    query = select(Topico.id).where(Topico.uc_id == uc_id, func.lower(Topico.nome) == nome.lower())
    if ignorar_id is not None:
        query = query.where(Topico.id != ignorar_id)
    return await session.scalar(query) is not None


async def listar_topicos(session: AsyncSession, uc_id: uuid.UUID) -> list[Topico]:
    await _garantir_uc(session, uc_id)
    result = await session.scalars(
        select(Topico).where(Topico.uc_id == uc_id).order_by(Topico.ordem, Topico.nome)
    )
    return list(result)


async def obter_topico(session: AsyncSession, topico_id: uuid.UUID) -> Topico:
    topico = await session.get(Topico, topico_id)
    if topico is None:
        raise TopicoNaoEncontrado
    return topico


async def criar_topico(session: AsyncSession, uc_id: uuid.UUID, dados: TopicoCreate) -> Topico:
    await _garantir_uc(session, uc_id)
    if await _nome_em_uso(session, uc_id, dados.nome):
        raise NomeDuplicado
    ultima_ordem = await session.scalar(select(func.max(Topico.ordem)).where(Topico.uc_id == uc_id))
    topico = Topico(
        uc_id=uc_id,
        nome=dados.nome,
        descricao=dados.descricao,
        ordem=0 if ultima_ordem is None else ultima_ordem + 1,
    )
    session.add(topico)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise NomeDuplicado from None
    await session.refresh(topico)
    return topico


async def atualizar_topico(
    session: AsyncSession, topico_id: uuid.UUID, dados: TopicoUpdate
) -> Topico:
    topico = await obter_topico(session, topico_id)
    alteracoes = dados.model_dump(exclude_unset=True)
    if alteracoes.get("nome") is None:
        alteracoes.pop("nome", None)
    novo_nome = alteracoes.get("nome")
    if novo_nome is not None and await _nome_em_uso(session, topico.uc_id, novo_nome, topico_id):
        raise NomeDuplicado
    for campo, valor in alteracoes.items():
        setattr(topico, campo, valor)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise NomeDuplicado from None
    await session.refresh(topico)
    return topico


async def reordenar_topicos(
    session: AsyncSession, uc_id: uuid.UUID, topico_ids: list[uuid.UUID]
) -> list[Topico]:
    """Critério 4: organiza os tópicos da UC pela ordem indicada."""
    topicos = await listar_topicos(session, uc_id)
    por_id = {topico.id: topico for topico in topicos}
    if len(topico_ids) != len(set(topico_ids)) or set(topico_ids) != set(por_id):
        raise OrdemInvalida
    for posicao, topico_id in enumerate(topico_ids):
        por_id[topico_id].ordem = posicao
    await session.commit()
    return [por_id[topico_id] for topico_id in topico_ids]


async def remover_topico(session: AsyncSession, topico_id: uuid.UUID) -> None:
    topico = await obter_topico(session, topico_id)
    await session.delete(topico)
    try:
        await session.commit()
    except IntegrityError:
        # Critério 7: as notas de estudo ligam-se ao tópico com ON DELETE RESTRICT,
        # por isso um tópico com notas não pode ser apagado (RN-032, RN-036).
        await session.rollback()
        raise TopicoComNotas from None
