"""Testes de permissões e validação das associações académicas (US-017, #105)."""

import uuid

import pytest
from httpx import AsyncClient

CURSOS_URL = "/api/v1/cursos"
UNIDADES_URL = "/api/v1/unidades-curriculares"

ADMIN = {"X-Dev-Role": "administrador"}
ESTUDANTE = {"X-Dev-Role": "estudante"}


@pytest.mark.parametrize("operacao", ["criar", "atualizar"])
async def test_estudante_nao_pode_modificar_associacao(client: AsyncClient, operacao: str) -> None:
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

    if operacao == "criar":
        response = await client.post(
            UNIDADES_URL,
            json={
                "codigo": "UC-ESTUDANTE",
                "nome": "Unidade Não Autorizada",
                "curso_id": curso_id,
            },
            headers=ESTUDANTE,
        )
    else:
        response = await client.patch(
            f"{UNIDADES_URL}/{unidade_id}",
            json={"curso_id": curso_id},
            headers=ESTUDANTE,
        )

    assert response.status_code == 403

    consulta = await client.get(f"{UNIDADES_URL}/{unidade_id}", headers=ADMIN)
    assert consulta.status_code == 200
    assert consulta.json()["curso_id"] is None


async def test_sem_autenticacao_nao_pode_alterar_associacao(
    client: AsyncClient,
) -> None:
    response = await client.patch(
        f"{UNIDADES_URL}/{uuid.uuid4()}",
        json={"curso_id": str(uuid.uuid4())},
    )

    assert response.status_code == 401


async def test_atualizacao_invalida_preserva_associacao(
    client: AsyncClient,
) -> None:
    curso = await client.post(
        CURSOS_URL,
        json={"codigo": "LEI-VALIDO", "nome": "Curso Válido"},
        headers=ADMIN,
    )
    assert curso.status_code == 201, curso.text
    curso_id = curso.json()["id"]

    unidade = await client.post(
        UNIDADES_URL,
        json={
            "codigo": "UC-VALIDA",
            "nome": "Unidade Original",
            "curso_id": curso_id,
        },
        headers=ADMIN,
    )
    assert unidade.status_code == 201, unidade.text
    unidade_id = unidade.json()["id"]

    response = await client.patch(
        f"{UNIDADES_URL}/{unidade_id}",
        json={
            "nome": "Nome Não Deve Ser Guardado",
            "curso_id": str(uuid.uuid4()),
        },
        headers=ADMIN,
    )
    assert response.status_code == 404

    consulta = await client.get(f"{UNIDADES_URL}/{unidade_id}", headers=ADMIN)
    assert consulta.status_code == 200
    assert consulta.json()["curso_id"] == curso_id
    assert consulta.json()["nome"] == "Unidade Original"


@pytest.mark.parametrize("operacao", ["criar", "atualizar"])
async def test_curso_id_com_formato_invalido(client: AsyncClient, operacao: str) -> None:
    if operacao == "criar":
        response = await client.post(
            UNIDADES_URL,
            json={
                "codigo": "UC-ID-INVALIDO",
                "nome": "Unidade de Teste",
                "curso_id": "identificador-invalido",
            },
            headers=ADMIN,
        )
    else:
        response = await client.patch(
            f"{UNIDADES_URL}/{uuid.uuid4()}",
            json={"curso_id": "identificador-invalido"},
            headers=ADMIN,
        )

    assert response.status_code == 422
