"""Testes da US-015 — gestão de cursos."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import Column, ForeignKey, Table, Uuid, insert
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from backend.app.core.db_base import Base

URL = "/api/v1/cursos"
ADMIN = {"X-Dev-Role": "administrador"}
ESTUDANTE = {"X-Dev-Role": "estudante"}


async def criar(client: AsyncClient, codigo: str = "8295", nome: str = "Eng. Informática") -> dict:
    response = await client.post(URL, json={"codigo": codigo, "nome": nome}, headers=ADMIN)
    assert response.status_code == 201, response.text
    return response.json()


# Critério 1 e 5: criar com informação identificadora.
async def test_administrador_cria_curso(client: AsyncClient) -> None:
    curso = await criar(client, codigo="  8295 ", nome="  Engenharia Informática ")
    assert curso["codigo"] == "8295"
    assert curso["nome"] == "Engenharia Informática"
    uuid.UUID(curso["id"])


@pytest.mark.parametrize(
    "payload", [{"codigo": "", "nome": "X"}, {"codigo": "1", "nome": "   "}, {"nome": "X"}]
)
async def test_rejeita_dados_invalidos(client: AsyncClient, payload: dict) -> None:
    response = await client.post(URL, json=payload, headers=ADMIN)
    assert response.status_code == 422


# Critério 7: consistência — o código é único.
async def test_rejeita_codigo_duplicado(client: AsyncClient) -> None:
    await criar(client, codigo="8295")
    response = await client.post(URL, json={"codigo": "8295", "nome": "Outro"}, headers=ADMIN)
    assert response.status_code == 409


# Critério 2: ver os cursos.
async def test_lista_e_mostra_cursos(client: AsyncClient) -> None:
    b = await criar(client, codigo="2", nome="Matemática")
    a = await criar(client, codigo="1", nome="Biologia")
    lista = await client.get(URL, headers=ESTUDANTE)
    assert lista.status_code == 200
    assert [c["id"] for c in lista.json()] == [a["id"], b["id"]]

    detalhe = await client.get(f"{URL}/{a['id']}", headers=ESTUDANTE)
    assert detalhe.status_code == 200
    assert detalhe.json()["nome"] == "Biologia"


async def test_curso_inexistente_devolve_404(client: AsyncClient) -> None:
    response = await client.get(f"{URL}/{uuid.uuid4()}", headers=ADMIN)
    assert response.status_code == 404


# Critério 3: atualizar.
async def test_atualiza_curso(client: AsyncClient) -> None:
    curso = await criar(client)
    response = await client.patch(f"{URL}/{curso['id']}", json={"nome": "LEI"}, headers=ADMIN)
    assert response.status_code == 200
    assert response.json() == {**curso, "nome": "LEI"}


async def test_atualizar_para_codigo_existente_devolve_409(client: AsyncClient) -> None:
    await criar(client, codigo="1", nome="A")
    outro = await criar(client, codigo="2", nome="B")
    response = await client.patch(f"{URL}/{outro['id']}", json={"codigo": "1"}, headers=ADMIN)
    assert response.status_code == 409


# Critério 4: remover.
async def test_remove_curso_sem_associacoes(client: AsyncClient) -> None:
    curso = await criar(client)
    response = await client.delete(f"{URL}/{curso['id']}", headers=ADMIN)
    assert response.status_code == 204
    assert (await client.get(f"{URL}/{curso['id']}", headers=ADMIN)).status_code == 404


async def test_nao_remove_curso_com_associacoes(
    client: AsyncClient, engine: AsyncEngine, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    # Simula a futura ligação curso–UC (US-017), que usará ON DELETE RESTRICT.
    ligacao = Table(
        "test_curso_uc",
        Base.metadata,
        Column("curso_id", Uuid, ForeignKey("curso.id", ondelete="RESTRICT")),
        extend_existing=True,
    )
    try:
        async with engine.begin() as connection:
            await connection.run_sync(ligacao.create)
        curso = await criar(client)
        async with session_factory() as session:
            await session.execute(insert(ligacao).values(curso_id=uuid.UUID(curso["id"])))
            await session.commit()

        response = await client.delete(f"{URL}/{curso['id']}", headers=ADMIN)
        assert response.status_code == 409
        assert (await client.get(f"{URL}/{curso['id']}", headers=ADMIN)).status_code == 200
    finally:
        Base.metadata.remove(ligacao)


# Critério 6: só utilizadores com permissões gerem cursos.
@pytest.mark.parametrize("method", ["post", "patch", "delete"])
async def test_estudante_nao_pode_gerir_cursos(client: AsyncClient, method: str) -> None:
    curso = await criar(client)
    kwargs = {"headers": ESTUDANTE}
    if method != "delete":
        kwargs["json"] = {"codigo": "9", "nome": "X"}
    target = URL if method == "post" else f"{URL}/{curso['id']}"
    response = await getattr(client, method)(target, **kwargs)
    assert response.status_code == 403


async def test_sem_papel_devolve_401(client: AsyncClient) -> None:
    assert (await client.get(URL)).status_code == 401
    assert (await client.post(URL, json={"codigo": "1", "nome": "A"})).status_code == 401
