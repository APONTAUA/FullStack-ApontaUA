"""Testes da US-018 — gestão de períodos académicos."""

import uuid

import pytest
from httpx import AsyncClient

URL_ANOS = "/api/v1/anos-letivos"

ADMIN = {"X-Dev-Role": "administrador"}
ESTUDANTE = {"X-Dev-Role": "estudante"}


async def criar_ano(
    client: AsyncClient,
    inicio: int = 2026,
    fim: int = 2027,
) -> dict:
    response = await client.post(
        URL_ANOS,
        json={"ano_inicio": inicio, "ano_fim": fim},
        headers=ADMIN,
    )

    assert response.status_code == 201, response.text
    return response.json()


async def test_administrador_cria_ano_letivo(client: AsyncClient) -> None:
    ano = await criar_ano(client)

    assert ano["ano_inicio"] == 2026
    assert ano["ano_fim"] == 2027
    uuid.UUID(ano["id"])


@pytest.mark.parametrize(
    "inicio,fim",
    [
        (2026, 2026),
        (2026, 2028),
        (2026, 2025),
    ],
)
async def test_rejeita_anos_nao_consecutivos(
    client: AsyncClient,
    inicio: int,
    fim: int,
) -> None:
    response = await client.post(
        URL_ANOS,
        json={"ano_inicio": inicio, "ano_fim": fim},
        headers=ADMIN,
    )

    assert response.status_code == 422


async def test_rejeita_ano_letivo_duplicado(client: AsyncClient) -> None:
    await criar_ano(client)

    response = await client.post(
        URL_ANOS,
        json={"ano_inicio": 2026, "ano_fim": 2027},
        headers=ADMIN,
    )

    assert response.status_code == 409


async def test_lista_e_consulta_anos_letivos(client: AsyncClient) -> None:
    segundo = await criar_ano(client, 2027, 2028)
    primeiro = await criar_ano(client, 2025, 2026)

    response = await client.get(URL_ANOS, headers=ESTUDANTE)

    assert response.status_code == 200
    assert [ano["id"] for ano in response.json()] == [
        primeiro["id"],
        segundo["id"],
    ]

    detalhe = await client.get(
        f"{URL_ANOS}/{primeiro['id']}",
        headers=ESTUDANTE,
    )

    assert detalhe.status_code == 200
    assert detalhe.json() == primeiro


async def test_atualiza_ano_letivo(client: AsyncClient) -> None:
    ano = await criar_ano(client)

    response = await client.patch(
        f"{URL_ANOS}/{ano['id']}",
        json={"ano_inicio": 2027, "ano_fim": 2028},
        headers=ADMIN,
    )

    assert response.status_code == 200
    assert response.json()["ano_inicio"] == 2027
    assert response.json()["ano_fim"] == 2028


async def test_ano_letivo_inexistente_devolve_404(
    client: AsyncClient,
) -> None:
    response = await client.get(
        f"{URL_ANOS}/{uuid.uuid4()}",
        headers=ESTUDANTE,
    )

    assert response.status_code == 404

URL_SEMESTRES = "/api/v1/semestres"


async def criar_semestre(
    client: AsyncClient,
    ano_id: str,
    numero: int = 1,
) -> dict:
    response = await client.post(
        URL_SEMESTRES,
        json={"numero": numero, "ano_letivo_id": ano_id},
        headers=ADMIN,
    )

    assert response.status_code == 201, response.text
    return response.json()


async def test_administrador_cria_semestres(client: AsyncClient) -> None:
    ano = await criar_ano(client)

    primeiro = await criar_semestre(client, ano["id"], 1)
    segundo = await criar_semestre(client, ano["id"], 2)

    assert primeiro["numero"] == 1
    assert segundo["numero"] == 2
    assert primeiro["ano_letivo_id"] == ano["id"]
    assert segundo["ano_letivo_id"] == ano["id"]


@pytest.mark.parametrize("numero", [0, 3, -1])
async def test_rejeita_numero_semestre_invalido(
    client: AsyncClient,
    numero: int,
) -> None:
    ano = await criar_ano(client)

    response = await client.post(
        URL_SEMESTRES,
        json={"numero": numero, "ano_letivo_id": ano["id"]},
        headers=ADMIN,
    )

    assert response.status_code == 422


async def test_rejeita_semestre_duplicado(client: AsyncClient) -> None:
    ano = await criar_ano(client)
    await criar_semestre(client, ano["id"], 1)

    response = await client.post(
        URL_SEMESTRES,
        json={"numero": 1, "ano_letivo_id": ano["id"]},
        headers=ADMIN,
    )

    assert response.status_code == 409

async def test_lista_semestres_de_ano_letivo(client: AsyncClient) -> None:
    ano = await criar_ano(client)

    segundo = await criar_semestre(client, ano["id"], 2)
    primeiro = await criar_semestre(client, ano["id"], 1)

    response = await client.get(
        f"{URL_ANOS}/{ano['id']}/semestres",
        headers=ESTUDANTE,
    )

    assert response.status_code == 200
    assert [s["id"] for s in response.json()] == [
        primeiro["id"],
        segundo["id"],
    ]


async def test_consulta_semestre(client: AsyncClient) -> None:
    ano = await criar_ano(client)
    semestre = await criar_semestre(client, ano["id"])

    response = await client.get(
        f"{URL_SEMESTRES}/{semestre['id']}",
        headers=ESTUDANTE,
    )

    assert response.status_code == 200
    assert response.json() == semestre


async def test_atualiza_semestre(client: AsyncClient) -> None:
    ano = await criar_ano(client)
    semestre = await criar_semestre(client, ano["id"], 1)

    response = await client.patch(
        f"{URL_SEMESTRES}/{semestre['id']}",
        json={"numero": 2},
        headers=ADMIN,
    )

    assert response.status_code == 200
    assert response.json()["numero"] == 2


async def test_semestre_inexistente_devolve_404(
    client: AsyncClient,
) -> None:
    response = await client.get(
        f"{URL_SEMESTRES}/{uuid.uuid4()}",
        headers=ESTUDANTE,
    )

    assert response.status_code == 404

URL_UNIDADES = "/api/v1/unidades-curriculares"


async def test_associa_unidade_curricular_a_semestre(
    client: AsyncClient,
) -> None:
    ano = await criar_ano(client)
    semestre = await criar_semestre(client, ano["id"])

    unidade_response = await client.post(
        URL_UNIDADES,
        json={
            "codigo": "US018-001",
            "nome": "Programação",
        },
        headers=ADMIN,
    )

    assert unidade_response.status_code == 201, unidade_response.text
    unidade = unidade_response.json()

    response = await client.post(
        f"{URL_SEMESTRES}/{semestre['id']}/unidades-curriculares",
        json={
            "unidade_curricular_id": unidade["id"],
            "semestre_id": semestre["id"],
        },
        headers=ADMIN,
    )

    assert response.status_code == 201, response.text
    assert response.json()["unidade_curricular_id"] == unidade["id"]
    assert response.json()["semestre_id"] == semestre["id"]
    uuid.UUID(response.json()["id"])

async def test_lista_unidades_curriculares_do_semestre(
    client: AsyncClient,
) -> None:
    ano = await criar_ano(client)
    semestre = await criar_semestre(client, ano["id"])

    response = await client.post(
        URL_UNIDADES,
        json={
            "codigo": "US018-002",
            "nome": "Bases de Dados",
        },
        headers=ADMIN,
    )

    assert response.status_code == 201, response.text
    unidade = response.json()

    associacao = await client.post(
        f"{URL_SEMESTRES}/{semestre['id']}/unidades-curriculares",
        json={
            "unidade_curricular_id": unidade["id"],
            "semestre_id": semestre["id"],
        },
        headers=ADMIN,
    )

    assert associacao.status_code == 201, associacao.text

    lista = await client.get(
        f"{URL_SEMESTRES}/{semestre['id']}/unidades-curriculares",
        headers=ESTUDANTE,
    )

    assert lista.status_code == 200
    assert len(lista.json()) == 1
    assert lista.json()[0]["unidade_curricular_id"] == unidade["id"]
    assert lista.json()[0]["semestre_id"] == semestre["id"]

async def test_rejeita_associacao_duplicada(
    client: AsyncClient,
) -> None:
    ano = await criar_ano(client)
    semestre = await criar_semestre(client, ano["id"])

    response = await client.post(
        URL_UNIDADES,
        json={
            "codigo": "US018-003",
            "nome": "Redes de Computadores",
        },
        headers=ADMIN,
    )

    assert response.status_code == 201, response.text
    unidade = response.json()

    url = f"{URL_SEMESTRES}/{semestre['id']}/unidades-curriculares"

    dados = {
        "unidade_curricular_id": unidade["id"],
        "semestre_id": semestre["id"],
    }

    primeira = await client.post(url, json=dados, headers=ADMIN)
    assert primeira.status_code == 201, primeira.text

    segunda = await client.post(url, json=dados, headers=ADMIN)
    assert segunda.status_code == 409

async def test_remove_associacao_unidade_semestre(
    client: AsyncClient,
) -> None:
    ano = await criar_ano(client)
    semestre = await criar_semestre(client, ano["id"])

    response = await client.post(
        URL_UNIDADES,
        json={
            "codigo": "US018-004",
            "nome": "Sistemas Operativos",
        },
        headers=ADMIN,
    )
    assert response.status_code == 201, response.text
    unidade = response.json()

    url = f"{URL_SEMESTRES}/{semestre['id']}/unidades-curriculares"

    associacao = await client.post(
        url,
        json={
            "unidade_curricular_id": unidade["id"],
            "semestre_id": semestre["id"],
        },
        headers=ADMIN,
    )
    assert associacao.status_code == 201, associacao.text

    associacao_id = associacao.json()["id"]

    remocao = await client.delete(
        f"{URL_SEMESTRES}/associacoes/{associacao_id}",
        headers=ADMIN,
    )
    assert remocao.status_code == 204

    lista = await client.get(url, headers=ESTUDANTE)
    assert lista.status_code == 200
    assert lista.json() == []

@pytest.mark.parametrize(
    "method,url,payload",
    [
        ("post", URL_ANOS, {"ano_inicio": 2026, "ano_fim": 2027}),
        ("patch", f"{URL_ANOS}/{uuid.uuid4()}", {"ano_inicio": 2027}),
        ("post", URL_SEMESTRES, {"numero": 1, "ano_letivo_id": str(uuid.uuid4())}),
        ("patch", f"{URL_SEMESTRES}/{uuid.uuid4()}", {"numero": 2}),
        (
            "post",
            f"{URL_SEMESTRES}/{uuid.uuid4()}/unidades-curriculares",
            {
                "semestre_id": str(uuid.uuid4()),
                "unidade_curricular_id": str(uuid.uuid4()),
            },
        ),
        ("delete", f"{URL_SEMESTRES}/associacoes/{uuid.uuid4()}", None),
    ],
)
async def test_estudante_nao_pode_gerir_periodos(
    client: AsyncClient,
    method: str,
    url: str,
    payload: dict | None,
) -> None:
    kwargs = {"headers": ESTUDANTE}

    if payload is not None:
        kwargs["json"] = payload

    response = await getattr(client, method)(url, **kwargs)

    assert response.status_code == 403
@pytest.mark.parametrize(
    "method,url,payload",
    [
        ("get", URL_ANOS, None),
        ("post", URL_ANOS, {"ano_inicio": 2026, "ano_fim": 2027}),
        ("get", f"{URL_ANOS}/{uuid.uuid4()}", None),
        ("post", URL_SEMESTRES, {"numero": 1, "ano_letivo_id": str(uuid.uuid4())}),
        ("get", f"{URL_SEMESTRES}/{uuid.uuid4()}", None),
        ("delete", f"{URL_SEMESTRES}/associacoes/{uuid.uuid4()}", None),
    ],
)
async def test_sem_autenticacao_devolve_401(
    client: AsyncClient,
    method: str,
    url: str,
    payload: dict | None,
) -> None:
    kwargs = {}

    if payload is not None:
        kwargs["json"] = payload

    response = await getattr(client, method)(url, **kwargs)

    assert response.status_code == 401

async def test_consulta_periodos_de_unidade_curricular(
    client: AsyncClient,
) -> None:
    ano = await criar_ano(client)
    semestre = await criar_semestre(client, ano["id"])

    resposta_unidade = await client.post(
        URL_UNIDADES,
        json={
            "codigo": "US018-PER",
            "nome": "Computação Distribuída",
        },
        headers=ADMIN,
    )
    assert resposta_unidade.status_code == 201, resposta_unidade.text
    unidade = resposta_unidade.json()

    resposta_associacao = await client.post(
        f"{URL_SEMESTRES}/{semestre['id']}/unidades-curriculares",
        json={
            "unidade_curricular_id": unidade["id"],
            "semestre_id": semestre["id"],
        },
        headers=ADMIN,
    )
    assert resposta_associacao.status_code == 201, resposta_associacao.text

    resposta = await client.get(
        f"{URL_UNIDADES}/{unidade['id']}/periodos",
        headers=ESTUDANTE,
    )

    assert resposta.status_code == 200, resposta.text

    periodos = resposta.json()
    assert len(periodos) == 1
    assert periodos[0]["unidade_curricular_id"] == unidade["id"]
    assert periodos[0]["semestre_id"] == semestre["id"]
    assert periodos[0]["numero_semestre"] == semestre["numero"]
    assert periodos[0]["ano_letivo_id"] == ano["id"]
    assert periodos[0]["ano_inicio"] == ano["ano_inicio"]
    assert periodos[0]["ano_fim"] == ano["ano_fim"]
