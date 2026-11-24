"""Testes da US-019 — gestão de tópicos."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import Column, ForeignKey, Table, Uuid, insert
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from backend.app.core.db_base import Base
from backend.app.modules.academic.models import UnidadeCurricular

ADMIN = {"X-Dev-Role": "administrador"}
ESTUDANTE = {"X-Dev-Role": "estudante"}


@pytest.fixture
async def uc_id(session_factory: async_sessionmaker[AsyncSession]) -> uuid.UUID:
    # A UC é criada diretamente na base de dados: a sua API pertence à US-016.
    async with session_factory() as session:
        uc = UnidadeCurricular(codigo="40337", nome="Projeto em Engenharia Informática")
        session.add(uc)
        await session.commit()
        return uc.id


def topicos_url(uc: uuid.UUID) -> str:
    return f"/api/v1/unidades-curriculares/{uc}/topicos"


async def criar(client: AsyncClient, uc: uuid.UUID, nome: str, **extra: str) -> dict:
    response = await client.post(topicos_url(uc), json={"nome": nome, **extra}, headers=ADMIN)
    assert response.status_code == 201, response.text
    return response.json()


# Critério 1: criar tópicos dentro de UCs existentes.
async def test_cria_topico_na_uc(client: AsyncClient, uc_id: uuid.UUID) -> None:
    topico = await criar(client, uc_id, "  Integrais ", descricao="  Cálculo integral  ")
    assert topico["nome"] == "Integrais"
    assert topico["descricao"] == "Cálculo integral"
    assert topico["uc_id"] == str(uc_id)
    assert topico["ordem"] == 0


async def test_descricao_vazia_fica_nula(client: AsyncClient, uc_id: uuid.UUID) -> None:
    topico = await criar(client, uc_id, "Limites", descricao="   ")
    assert topico["descricao"] is None


@pytest.mark.parametrize("payload", [{"nome": ""}, {"nome": "   "}, {}, {"nome": "A", "x": 1}])
async def test_rejeita_dados_invalidos(
    client: AsyncClient, uc_id: uuid.UUID, payload: dict
) -> None:
    response = await client.post(topicos_url(uc_id), json=payload, headers=ADMIN)
    assert response.status_code == 422


# Critérios 5 e 6: um tópico pertence sempre a uma UC válida.
async def test_uc_inexistente_devolve_404(client: AsyncClient) -> None:
    uc = uuid.uuid4()
    assert (
        await client.post(topicos_url(uc), json={"nome": "X"}, headers=ADMIN)
    ).status_code == 404
    assert (await client.get(topicos_url(uc), headers=ADMIN)).status_code == 404


async def test_nome_repetido_na_mesma_uc_devolve_409(client: AsyncClient, uc_id: uuid.UUID) -> None:
    await criar(client, uc_id, "Integrais")
    response = await client.post(topicos_url(uc_id), json={"nome": "integrais"}, headers=ADMIN)
    assert response.status_code == 409


async def test_mesmo_nome_em_ucs_diferentes_e_permitido(
    client: AsyncClient, uc_id: uuid.UUID, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    async with session_factory() as session:
        outra = UnidadeCurricular(codigo="40338", nome="Outra UC")
        session.add(outra)
        await session.commit()
        outra_id = outra.id
    await criar(client, uc_id, "Introdução")
    await criar(client, outra_id, "Introdução")


# Critério 2: ver os tópicos de uma UC, pela ordem definida.
async def test_lista_topicos_por_ordem(client: AsyncClient, uc_id: uuid.UUID) -> None:
    a = await criar(client, uc_id, "Limites")
    b = await criar(client, uc_id, "Derivadas")
    response = await client.get(topicos_url(uc_id), headers=ESTUDANTE)
    assert response.status_code == 200
    assert [t["id"] for t in response.json()] == [a["id"], b["id"]]
    assert [t["ordem"] for t in response.json()] == [0, 1]

    detalhe = await client.get(f"/api/v1/topicos/{a['id']}", headers=ESTUDANTE)
    assert detalhe.status_code == 200
    assert detalhe.json()["nome"] == "Limites"


async def test_topico_inexistente_devolve_404(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/topicos/{uuid.uuid4()}", headers=ADMIN)
    assert response.status_code == 404


# Critério 3: atualizar.
async def test_atualiza_topico(client: AsyncClient, uc_id: uuid.UUID) -> None:
    topico = await criar(client, uc_id, "Limites")
    response = await client.patch(
        f"/api/v1/topicos/{topico['id']}",
        json={"nome": "Limites e continuidade", "descricao": "Cap. 1"},
        headers=ADMIN,
    )
    assert response.status_code == 200
    assert response.json() == {**topico, "nome": "Limites e continuidade", "descricao": "Cap. 1"}


async def test_atualizar_para_nome_existente_devolve_409(
    client: AsyncClient, uc_id: uuid.UUID
) -> None:
    await criar(client, uc_id, "Limites")
    outro = await criar(client, uc_id, "Derivadas")
    response = await client.patch(
        f"/api/v1/topicos/{outro['id']}", json={"nome": "LIMITES"}, headers=ADMIN
    )
    assert response.status_code == 409


async def test_nao_permite_mudar_a_uc_do_topico(client: AsyncClient, uc_id: uuid.UUID) -> None:
    topico = await criar(client, uc_id, "Limites")
    response = await client.patch(
        f"/api/v1/topicos/{topico['id']}", json={"uc_id": str(uuid.uuid4())}, headers=ADMIN
    )
    assert response.status_code == 422


# Critério 4: organizar os tópicos dentro da UC.
async def test_reordena_topicos(client: AsyncClient, uc_id: uuid.UUID) -> None:
    a = await criar(client, uc_id, "A")
    b = await criar(client, uc_id, "B")
    c = await criar(client, uc_id, "C")
    nova = [c["id"], a["id"], b["id"]]
    response = await client.put(
        f"{topicos_url(uc_id)}/ordem", json={"topico_ids": nova}, headers=ADMIN
    )
    assert response.status_code == 200
    lista = await client.get(topicos_url(uc_id), headers=ADMIN)
    assert [t["id"] for t in lista.json()] == nova


@pytest.mark.parametrize("caso", ["em_falta", "repetido", "de_outra_uc"])
async def test_reordenar_exige_todos_os_topicos_uma_vez(
    client: AsyncClient, uc_id: uuid.UUID, caso: str
) -> None:
    a = await criar(client, uc_id, "A")
    b = await criar(client, uc_id, "B")
    ids = {
        "em_falta": [a["id"]],
        "repetido": [a["id"], a["id"], b["id"]],
        "de_outra_uc": [a["id"], b["id"], str(uuid.uuid4())],
    }[caso]
    response = await client.put(
        f"{topicos_url(uc_id)}/ordem", json={"topico_ids": ids}, headers=ADMIN
    )
    assert response.status_code == 422


# Remoção e critério 7: consistência com as notas de estudo.
async def test_remove_topico_sem_notas(client: AsyncClient, uc_id: uuid.UUID) -> None:
    topico = await criar(client, uc_id, "Limites")
    assert (
        await client.delete(f"/api/v1/topicos/{topico['id']}", headers=ADMIN)
    ).status_code == 204
    assert (await client.get(f"/api/v1/topicos/{topico['id']}", headers=ADMIN)).status_code == 404


async def test_nao_remove_topico_com_notas(
    client: AsyncClient,
    uc_id: uuid.UUID,
    engine: AsyncEngine,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    # Simula a futura ligação material–tópico (EPIC-04), com ON DELETE RESTRICT.
    notas = Table(
        "test_material",
        Base.metadata,
        Column("topico_id", Uuid, ForeignKey("topico.id", ondelete="RESTRICT")),
        extend_existing=True,
    )
    try:
        async with engine.begin() as connection:
            await connection.run_sync(notas.create)
        topico = await criar(client, uc_id, "Limites")
        async with session_factory() as session:
            await session.execute(insert(notas).values(topico_id=uuid.UUID(topico["id"])))
            await session.commit()

        response = await client.delete(f"/api/v1/topicos/{topico['id']}", headers=ADMIN)
        assert response.status_code == 409
        assert (
            await client.get(f"/api/v1/topicos/{topico['id']}", headers=ADMIN)
        ).status_code == 200
    finally:
        Base.metadata.remove(notas)


async def test_nao_remove_uc_com_topicos(
    client: AsyncClient, uc_id: uuid.UUID, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    from sqlalchemy.exc import IntegrityError

    await criar(client, uc_id, "Limites")
    async with session_factory() as session:
        uc = await session.get(UnidadeCurricular, uc_id)
        await session.delete(uc)
        with pytest.raises(IntegrityError):
            await session.commit()


# Critério 8: só utilizadores com permissões gerem os tópicos.
async def test_estudante_nao_gere_topicos(client: AsyncClient, uc_id: uuid.UUID) -> None:
    topico = await criar(client, uc_id, "Limites")
    pedidos = [
        client.post(topicos_url(uc_id), json={"nome": "X"}, headers=ESTUDANTE),
        client.patch(f"/api/v1/topicos/{topico['id']}", json={"nome": "Y"}, headers=ESTUDANTE),
        client.put(
            f"{topicos_url(uc_id)}/ordem", json={"topico_ids": [topico["id"]]}, headers=ESTUDANTE
        ),
        client.delete(f"/api/v1/topicos/{topico['id']}", headers=ESTUDANTE),
    ]
    for pedido in pedidos:
        assert (await pedido).status_code == 403


async def test_sem_papel_devolve_401(client: AsyncClient, uc_id: uuid.UUID) -> None:
    assert (await client.get(topicos_url(uc_id))).status_code == 401
