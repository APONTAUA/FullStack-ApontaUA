"""Testes de permissões e validação das unidades curriculares (US-016, #97)."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import Column, ForeignKey, Table, Uuid, insert
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from backend.app.core.db_base import Base

URL = "/api/v1/unidades-curriculares"

ESTUDANTE = {"X-Dev-Role": "estudante"}


async def test_estudante_nao_pode_criar_unidade_curricular(client: AsyncClient) -> None:
    response = await client.post(
        URL,
        json={"codigo": "TEST-001", "nome": "Unidade Curricular de Teste"},
        headers=ESTUDANTE,
    )

    assert response.status_code == 403


@pytest.mark.parametrize("method", ["patch", "delete"])
async def test_estudante_nao_pode_alterar_unidade_curricular(
    client: AsyncClient, method: str
) -> None:
    unidade_id = "00000000-0000-0000-0000-000000000001"

    if method == "patch":
        response = await client.patch(
            f"{URL}/{unidade_id}",
            json={"nome": "Nome Alterado"},
            headers=ESTUDANTE,
        )
    else:
        response = await client.delete(
            f"{URL}/{unidade_id}",
            headers=ESTUDANTE,
        )

    assert response.status_code == 403


@pytest.mark.parametrize("method", ["get", "post", "patch", "delete"])
async def test_sem_papel_devolve_401(client: AsyncClient, method: str) -> None:
    unidade_id = "00000000-0000-0000-0000-000000000001"

    if method == "post":
        response = await client.post(
            URL,
            json={"codigo": "TEST-001", "nome": "Unidade de Teste"},
        )
    elif method == "patch":
        response = await client.patch(
            f"{URL}/{unidade_id}",
            json={"nome": "Nome Alterado"},
        )
    elif method == "delete":
        response = await client.delete(f"{URL}/{unidade_id}")
    else:
        response = await client.get(URL)

    assert response.status_code == 401


ADMIN = {"X-Dev-Role": "administrador"}


@pytest.mark.parametrize(
    "payload",
    [
        {"codigo": "", "nome": "Matemática"},
        {"codigo": "MAT", "nome": "   "},
        {"nome": "Matemática"},
        {"codigo": "MAT"},
        {"codigo": "MAT", "nome": "Matemática", "extra": "invalido"},
    ],
)
async def test_rejeita_dados_invalidos_na_criacao(client: AsyncClient, payload: dict) -> None:
    response = await client.post(URL, json=payload, headers=ADMIN)

    assert response.status_code == 422


@pytest.mark.parametrize("campo", ["codigo", "nome"])
async def test_rejeita_null_na_atualizacao(client: AsyncClient, campo: str) -> None:
    response = await client.post(
        URL,
        json={"codigo": "TEST-NULL", "nome": "Unidade de Teste"},
        headers=ADMIN,
    )
    assert response.status_code == 201, response.text

    unidade_id = response.json()["id"]

    response = await client.patch(
        f"{URL}/{unidade_id}",
        json={campo: None},
        headers=ADMIN,
    )

    assert response.status_code == 422


async def test_rejeita_codigo_duplicado_na_criacao(client: AsyncClient) -> None:
    dados = {"codigo": "UC-DUP-001", "nome": "Unidade Original"}

    primeira = await client.post(URL, json=dados, headers=ADMIN)
    assert primeira.status_code == 201, primeira.text

    segunda = await client.post(
        URL,
        json={"codigo": "UC-DUP-001", "nome": "Outra Unidade"},
        headers=ADMIN,
    )

    assert segunda.status_code == 409


async def test_rejeita_codigo_duplicado_na_atualizacao(client: AsyncClient) -> None:
    primeira = await client.post(
        URL,
        json={"codigo": "UC-001", "nome": "Primeira Unidade"},
        headers=ADMIN,
    )
    assert primeira.status_code == 201, primeira.text

    segunda = await client.post(
        URL,
        json={"codigo": "UC-002", "nome": "Segunda Unidade"},
        headers=ADMIN,
    )
    assert segunda.status_code == 201, segunda.text

    unidade_id = segunda.json()["id"]

    response = await client.patch(
        f"{URL}/{unidade_id}",
        json={"codigo": "UC-001"},
        headers=ADMIN,
    )

    assert response.status_code == 409


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
async def test_unidade_curricular_inexistente_devolve_404(client: AsyncClient, method: str) -> None:
    unidade_id = "00000000-0000-0000-0000-000000000001"
    url = f"{URL}/{unidade_id}"

    if method == "patch":
        response = await client.patch(
            url,
            json={"nome": "Nome Atualizado"},
            headers=ADMIN,
        )
    elif method == "delete":
        response = await client.delete(url, headers=ADMIN)
    else:
        response = await client.get(url, headers=ADMIN)

    assert response.status_code == 404


async def test_nao_remove_unidade_curricular_com_associacoes(
    client: AsyncClient,
    engine: AsyncEngine,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    # Simula uma associação académica protegida por uma chave estrangeira.
    ligacao = Table(
        "test_uc_associacao",
        Base.metadata,
        Column(
            "unidade_id",
            Uuid,
            ForeignKey("unidade_curricular.id", ondelete="RESTRICT"),
        ),
        extend_existing=True,
    )

    try:
        async with engine.begin() as connection:
            await connection.run_sync(ligacao.create)

        response = await client.post(
            URL,
            json={"codigo": "UC-ASSOC-001", "nome": "Unidade com Associação"},
            headers=ADMIN,
        )
        assert response.status_code == 201, response.text
        unidade_id = response.json()["id"]

        async with session_factory() as session:
            await session.execute(insert(ligacao).values(unidade_id=uuid.UUID(unidade_id)))
            await session.commit()

        response = await client.delete(
            f"{URL}/{unidade_id}",
            headers=ADMIN,
        )

        assert response.status_code == 409
        assert (await client.get(f"{URL}/{unidade_id}", headers=ADMIN)).status_code == 200
    finally:
        Base.metadata.remove(ligacao)
