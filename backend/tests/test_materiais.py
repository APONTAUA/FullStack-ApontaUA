"""Testes da US-022 — publicação de materiais pela comunidade."""

import hashlib
import io
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.app.core.config import settings
from backend.app.core.database import get_db_session
from backend.app.main import app
from backend.app.modules.academic.models import UnidadeCurricular
from backend.app.modules.academic.topicos.models import Topico
from backend.app.modules.materials.models import Material, VersaoMaterial, EstadoMaterial
from backend.app.modules.materials.router import get_armazenamento
from backend.app.modules.storage.models import StoredFile

URL = "/api/v1/materiais"
AUTOR = uuid.UUID("11111111-1111-4111-8111-111111111111")
PDF = b"%PDF-1.7\nconteudo de teste\n"


def headers(papel: str = "estudante", autor: uuid.UUID | str | None = AUTOR) -> dict[str, str]:
    result = {"X-Dev-Role": papel}
    if autor is not None:
        result["X-Dev-User-Id"] = str(autor)
    return result


class FakeStorage:
    def __init__(self) -> None:
        self.uploads: dict[str, dict] = {}
        self.deleted: list[str] = []

    async def upload(self, object_key, data, length, content_type, sha256=None) -> None:
        self.uploads[object_key] = {
            "data": data.read(),
            "length": length,
            "content_type": content_type,
            "sha256": sha256,
        }

    async def delete(self, object_key) -> None:
        self.deleted.append(object_key)


@pytest.fixture
def storage() -> FakeStorage:
    fake = FakeStorage()
    app.dependency_overrides[get_armazenamento] = lambda: fake
    return fake


@pytest.fixture
async def estrutura(session_factory: async_sessionmaker[AsyncSession]) -> dict[str, uuid.UUID]:
    async with session_factory() as session:
        uc = UnidadeCurricular(codigo="40337", nome="PEI")
        outra = UnidadeCurricular(codigo="40338", nome="Outra")
        session.add_all([uc, outra])
        await session.flush()
        topico = Topico(uc_id=uc.id, nome="Requisitos", ordem=0)
        topico_outra = Topico(uc_id=outra.id, nome="Outro tópico", ordem=0)
        session.add_all([topico, topico_outra])
        await session.commit()
        return {
            "uc": uc.id,
            "topico": topico.id,
            "outra_uc": outra.id,
            "topico_outra": topico_outra.id,
        }


def form(estrutura: dict[str, uuid.UUID], **extra: str) -> dict[str, str]:
    dados = {
        "titulo": "Resumo de requisitos",
        "categoria": "apontamentos",
        "uc_id": str(estrutura["uc"]),
        "topico_id": str(estrutura["topico"]),
    }
    dados.update(extra)
    return {k: v for k, v in dados.items() if v is not None}


def ficheiro(nome: str = "resumo.pdf", conteudo: bytes = PDF, tipo: str = "application/pdf"):
    return {"ficheiro": (nome, io.BytesIO(conteudo), tipo)}


async def publicar(client: AsyncClient, estrutura, *, h=None, files=None, **extra):
    return await client.post(
        URL, data=form(estrutura, **extra), files=files or ficheiro(), headers=h or headers()
    )


# Critérios 1, 4, 5 e 6: publicar, identificar o autor, registar a data e a origem comunidade.
async def test_publica_material(
    client: AsyncClient,
    storage: FakeStorage,
    estrutura,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    antes = datetime.now(UTC) - timedelta(seconds=5)
    response = await publicar(
        client,
        estrutura,
        descricao="  Capítulos 1 a 3  ",
        ano_letivo="2026/2027",
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["titulo"] == "Resumo de requisitos"
    assert body["descricao"] == "Capítulos 1 a 3"
    assert body["categoria"] == "apontamentos"
    assert body["origem"] == "comunidade"
    assert body["estado"] == "publicado"  # Critério 7: sem aprovação prévia
    assert body["ano_letivo"] == "2026/2027"
    assert body["uc_id"] == str(estrutura["uc"])
    assert body["topico_id"] == str(estrutura["topico"])
    assert body["autor_id"] == str(AUTOR)
    assert datetime.fromisoformat(body["publicado_em"]).replace(tzinfo=UTC) >= antes

    versao = body["versao_atual"]
    assert versao["numero"] == 1
    assert versao["ficheiro"] == {
        "nome_original": "resumo.pdf",
        "tipo": "application/pdf",
        "tamanho_bytes": len(PDF),
        "sha256": hashlib.sha256(PDF).hexdigest(),
    }

    [(key, upload)] = storage.uploads.items()
    assert key.startswith(f"materials/{body['id']}/v1/")
    assert upload["data"] == PDF
    assert upload["sha256"] == hashlib.sha256(PDF).hexdigest()

    async with session_factory() as session:
        material = await session.get(Material, uuid.UUID(body["id"]))
        assert material is not None
        [versao_db] = (await session.scalars(select(VersaoMaterial))).all()
        guardado = await session.get(StoredFile, versao_db.ficheiro_id)
        assert guardado.object_key == key
        assert versao_db.material_id == material.id


@pytest.mark.parametrize(
    "papel", ["estudante", "docente", "representante", "moderador", "administrador"]
)
async def test_utilizadores_autenticados_podem_publicar(
    client: AsyncClient, storage: FakeStorage, estrutura, papel: str
) -> None:
    response = await publicar(client, estrutura, h=headers(papel))
    assert response.status_code == 201


# Critérios 2 e 3: UC e tópico existentes, e o tópico pertence à UC.
async def test_uc_inexistente(client: AsyncClient, storage: FakeStorage, estrutura) -> None:
    response = await publicar(client, estrutura, uc_id=str(uuid.uuid4()))
    assert response.status_code == 404
    assert storage.uploads == {}


async def test_topico_inexistente(client: AsyncClient, storage: FakeStorage, estrutura) -> None:
    response = await publicar(client, estrutura, topico_id=str(uuid.uuid4()))
    assert response.status_code == 404


async def test_topico_de_outra_uc(client: AsyncClient, storage: FakeStorage, estrutura) -> None:
    response = await publicar(client, estrutura, topico_id=str(estrutura["topico_outra"]))
    assert response.status_code == 422
    assert "does not belong" in response.json()["detail"]
    assert storage.uploads == {}


# Critério 8: informação obrigatória em falta ou inválida.
@pytest.mark.parametrize(
    "extra",
    [
        {"titulo": None},
        {"titulo": "   "},
        {"categoria": "receita"},
        {"categoria": None},
        {"uc_id": "nao-e-uuid"},
        {"topico_id": None},
        {"ano_letivo": "2026/2028"},
        {"ano_letivo": "26/27"},
        {"campo_extra": "x"},
    ],
)
async def test_rejeita_metadados_invalidos(
    client: AsyncClient, storage: FakeStorage, estrutura, extra: dict
) -> None:
    response = await publicar(client, estrutura, **extra)
    assert response.status_code == 422
    assert storage.uploads == {}


async def test_rejeita_publicacao_sem_ficheiro(
    client: AsyncClient, storage: FakeStorage, estrutura
) -> None:
    response = await client.post(URL, data=form(estrutura), headers=headers())
    assert response.status_code == 422


async def test_rejeita_formato_nao_suportado(
    client: AsyncClient, storage: FakeStorage, estrutura
) -> None:
    response = await publicar(
        client, estrutura, files=ficheiro("programa.exe", b"MZ", "application/pdf")
    )
    assert response.status_code == 415
    assert "pdf" in response.json()["detail"]
    assert storage.uploads == {}


@pytest.mark.parametrize(
    ("nome", "tipo"),
    [
        ("NOTAS.PDF", "application/pdf"),
        ("apontamentos.md", "text/markdown"),
        (
            "slides.pptx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ),
        ("folha.xls", "application/vnd.ms-excel"),
        ("quadro.jpeg", "image/jpeg"),
        ("esquema.png", "image/png"),
    ],
)
async def test_tipo_vem_da_extensao(
    client: AsyncClient, storage: FakeStorage, estrutura, nome: str, tipo: str
) -> None:
    response = await publicar(
        client, estrutura, files=ficheiro(nome, b"conteudo", "application/octet-stream")
    )
    assert response.status_code == 201
    assert response.json()["versao_atual"]["ficheiro"]["tipo"] == tipo


async def test_rejeita_ficheiro_vazio(client: AsyncClient, storage: FakeStorage, estrutura) -> None:
    response = await publicar(client, estrutura, files=ficheiro(conteudo=b""))
    assert response.status_code == 422


async def test_rejeita_ficheiro_grande(
    client: AsyncClient, storage: FakeStorage, estrutura, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "max_upload_size_mb", 1)
    grande = b"x" * (1024 * 1024 + 1)
    response = await publicar(client, estrutura, files=ficheiro(conteudo=grande))
    assert response.status_code == 413
    assert storage.uploads == {}


async def test_nome_do_ficheiro_sem_pastas(
    client: AsyncClient, storage: FakeStorage, estrutura
) -> None:
    response = await publicar(client, estrutura, files=ficheiro("../../segredos/resumo.pdf"))
    assert response.status_code == 201
    assert response.json()["versao_atual"]["ficheiro"]["nome_original"] == "resumo.pdf"
    [key] = storage.uploads
    assert "segredos" not in key and ".." not in key


# Sem registo na base de dados, o ficheiro enviado para o MinIO é apagado.
async def test_apaga_ficheiro_se_a_base_de_dados_falhar(
    client: AsyncClient,
    storage: FakeStorage,
    estrutura,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def sessao_que_falha():
        async with session_factory() as session:

            async def commit_falhado() -> None:
                raise RuntimeError("falha simulada")

            session.commit = commit_falhado  # type: ignore[method-assign]
            yield session

    app.dependency_overrides[get_db_session] = sessao_que_falha
    response = await publicar(client, estrutura)
    assert response.status_code == 500

    [key] = storage.uploads
    assert storage.deleted == [key]
    async with session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(Material)) == 0


async def test_armazenamento_nao_configurado_devolve_503(client: AsyncClient, estrutura) -> None:
    response = await publicar(client, estrutura)
    assert response.status_code == 503


# Autor provisório: só com X-Dev-User-Id válido.
@pytest.mark.parametrize("autor", [None, "nao-e-uuid"])
async def test_autor_obrigatorio(
    client: AsyncClient, storage: FakeStorage, estrutura, autor
) -> None:
    response = await publicar(client, estrutura, h=headers(autor=autor))
    assert response.status_code == 401


async def test_sem_papel_devolve_401(client: AsyncClient, storage: FakeStorage, estrutura) -> None:
    response = await client.post(
        URL, data=form(estrutura), files=ficheiro(), headers={"X-Dev-User-Id": str(AUTOR)}
    )
    assert response.status_code == 401


# US-019, critério 7: um tópico com materiais não pode ser apagado.
async def test_topico_com_materiais_nao_pode_ser_apagado(
    client: AsyncClient, storage: FakeStorage, estrutura
) -> None:
    assert (await publicar(client, estrutura)).status_code == 201
    response = await client.delete(
        f"/api/v1/topicos/{estrutura['topico']}", headers=headers("administrador")
    )
    assert response.status_code == 409


# Atualização: as associações académicas permanecem consistentes após alterar metadados.


async def test_atualiza_metadados_preservando_contexto_academico(
    client: AsyncClient,
    storage: FakeStorage,
    estrutura,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    publicado = await publicar(client, estrutura)
    assert publicado.status_code == 201

    response = await client.patch(
        f"{URL}/{publicado.json()['id']}",
        json={"titulo": "Resumo atualizado", "descricao": "  Novo texto  "},
        headers=headers(),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["titulo"] == "Resumo atualizado"
    assert body["descricao"] == "Novo texto"
    assert body["uc_id"] == str(estrutura["uc"])
    assert body["topico_id"] == str(estrutura["topico"])


async def test_atualiza_reassociando_topico_da_mesma_uc(
    client: AsyncClient,
    storage: FakeStorage,
    estrutura,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    publicado = await publicar(client, estrutura)
    assert publicado.status_code == 201

    async with session_factory() as session:
        novo_topico = Topico(uc_id=estrutura["uc"], nome="Arquitetura", ordem=1)
        session.add(novo_topico)
        await session.commit()
        novo_topico_id = novo_topico.id

    response = await client.patch(
        f"{URL}/{publicado.json()['id']}",
        json={"uc_id": str(estrutura["uc"]), "topico_id": str(novo_topico_id)},
        headers=headers(),
    )

    assert response.status_code == 200, response.text
    assert response.json()["topico_id"] == str(novo_topico_id)
    assert response.json()["uc_id"] == str(estrutura["uc"])


@pytest.mark.parametrize(
    ("campo", "valor", "codigo", "detalhe"),
    [
        ("uc_id", str(uuid.uuid4()), 404, "Course unit not found"),
        ("topico_id", str(uuid.uuid4()), 404, "Topic not found"),
        ("topico_id", "topico_outra", 422, "does not belong"),
    ],
)
async def test_atualizacao_rejeita_associacao_invalida(
    client: AsyncClient,
    storage: FakeStorage,
    estrutura,
    campo: str,
    valor: str,
    codigo: int,
    detalhe: str,
) -> None:
    publicado = await publicar(client, estrutura)
    assert publicado.status_code == 201

    if valor == "topico_outra":
        valor = str(estrutura["topico_outra"])

    response = await client.patch(
        f"{URL}/{publicado.json()['id']}",
        json={campo: valor},
        headers=headers(),
    )

    assert response.status_code == codigo
    assert detalhe in response.json()["detail"]


async def test_atualiza_material_inexistente(client: AsyncClient) -> None:
    response = await client.patch(
        f"{URL}/{uuid.uuid4()}",
        json={"titulo": "Nota"},
        headers=headers(),
    )
    assert response.status_code == 404


# US-021 — consulta de materiais associados a tópicos.


async def test_lista_materiais_publicados_por_topico(
    client: AsyncClient,
    storage: FakeStorage,
    estrutura,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    publicado = await publicar(
        client, estrutura, titulo="Nota visível"
    )
    removido = await publicar(
        client, estrutura, titulo="Nota removida"
    )
    outro_topico = await publicar(
        client,
        estrutura,
        titulo="Nota de outra UC",
        uc_id=str(estrutura["outra_uc"]),
        topico_id=str(estrutura["topico_outra"]),
    )

    assert publicado.status_code == 201
    assert removido.status_code == 201
    assert outro_topico.status_code == 201

    async with session_factory() as session:
        material = await session.get(
            Material,
            uuid.UUID(removido.json()["id"]),
        )
        assert material is not None
        material.estado = EstadoMaterial.REMOVIDO
        await session.commit()

    response = await client.get(
        URL,
        params={"topico_id": str(estrutura["topico"])},
        headers=headers(),
    )

    assert response.status_code == 200, response.text

    materiais = response.json()

    assert len(materiais) == 1
    assert materiais[0]["id"] == publicado.json()["id"]
    assert materiais[0]["titulo"] == "Nota visível"
    assert materiais[0]["uc_id"] == str(estrutura["uc"])
    assert materiais[0]["topico_id"] == str(estrutura["topico"])
    assert materiais[0]["estado"] == "publicado"

    assert materiais[0]["versao_atual"]["numero"] == 1
    assert materiais[0]["versao_atual"]["ficheiro"]["nome_original"] == "resumo.pdf"


async def test_lista_materiais_rejeita_topico_inexistente(
    client: AsyncClient,
) -> None:
    response = await client.get(
        URL,
        params={"topico_id": str(uuid.uuid4())},
        headers=headers(),
    )

    assert response.status_code == 404
