"""Testes da API de associações entre unidades curriculares e cursos (US-017, #104)."""

import uuid

from httpx import AsyncClient

CURSOS_URL = "/api/v1/cursos"
UNIDADES_URL = "/api/v1/unidades-curriculares"
ADMIN = {"X-Dev-Role": "administrador"}


async def test_criar_e_consultar_unidade_com_curso(client: AsyncClient) -> None:
    curso = await client.post(
        CURSOS_URL,
        json={"codigo": "LEI-104", "nome": "Engenharia Informática"},
        headers=ADMIN,
    )
    assert curso.status_code == 201, curso.text
    curso_id = curso.json()["id"]

    unidade = await client.post(
        UNIDADES_URL,
        json={
            "codigo": "CD-104",
            "nome": "Computação Distribuída",
            "curso_id": curso_id,
        },
        headers=ADMIN,
    )
    assert unidade.status_code == 201, unidade.text
    assert unidade.json()["curso_id"] == curso_id

    unidade_id = unidade.json()["id"]

    consulta = await client.get(
        f"{UNIDADES_URL}/{unidade_id}",
        headers=ADMIN,
    )
    assert consulta.status_code == 200
    assert consulta.json()["curso_id"] == curso_id

    listagem = await client.get(UNIDADES_URL, headers=ADMIN)
    assert listagem.status_code == 200
    assert any(
        item["id"] == unidade_id and item["curso_id"] == curso_id for item in listagem.json()
    )


async def test_atualizar_e_remover_associacao(client: AsyncClient) -> None:
    curso = await client.post(
        CURSOS_URL,
        json={"codigo": "LEI-105", "nome": "Engenharia Informática"},
        headers=ADMIN,
    )
    assert curso.status_code == 201, curso.text
    curso_id = curso.json()["id"]

    unidade = await client.post(
        UNIDADES_URL,
        json={"codigo": "UC-105", "nome": "Unidade de Teste"},
        headers=ADMIN,
    )
    assert unidade.status_code == 201, unidade.text
    unidade_id = unidade.json()["id"]
    assert unidade.json()["curso_id"] is None

    associar = await client.patch(
        f"{UNIDADES_URL}/{unidade_id}",
        json={"curso_id": curso_id},
        headers=ADMIN,
    )
    assert associar.status_code == 200, associar.text
    assert associar.json()["curso_id"] == curso_id

    remover = await client.patch(
        f"{UNIDADES_URL}/{unidade_id}",
        json={"curso_id": None},
        headers=ADMIN,
    )
    assert remover.status_code == 200, remover.text
    assert remover.json()["curso_id"] is None

    consulta = await client.get(f"{UNIDADES_URL}/{unidade_id}", headers=ADMIN)
    assert consulta.json()["curso_id"] is None


async def test_criar_com_curso_inexistente_devolve_404(client: AsyncClient) -> None:
    response = await client.post(
        UNIDADES_URL,
        json={
            "codigo": "UC-INVALIDA",
            "nome": "Unidade Inválida",
            "curso_id": str(uuid.uuid4()),
        },
        headers=ADMIN,
    )
    assert response.status_code == 404


async def test_atualizar_com_curso_inexistente_devolve_404(client: AsyncClient) -> None:
    unidade = await client.post(
        UNIDADES_URL,
        json={"codigo": "UC-106", "nome": "Unidade de Teste"},
        headers=ADMIN,
    )
    assert unidade.status_code == 201, unidade.text

    response = await client.patch(
        f"{UNIDADES_URL}/{unidade.json()['id']}",
        json={"curso_id": str(uuid.uuid4())},
        headers=ADMIN,
    )
    assert response.status_code == 404
