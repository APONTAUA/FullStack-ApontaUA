import hashlib
import io
import logging
import uuid
from dataclasses import dataclass
from typing import Protocol

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.modules.academic.models import UnidadeCurricular
from backend.app.modules.academic.topicos.models import Topico
from backend.app.modules.materials.formats import nome_seguro, tipo_do_ficheiro
from backend.app.modules.materials.models import Material, OrigemMaterial, VersaoMaterial, EstadoMaterial
from backend.app.modules.materials.schemas import MaterialCreate, MaterialUpdate
from backend.app.modules.storage.models import StoredFile

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 1024


class Armazenamento(Protocol):
    """Parte do ObjectStorage (MinIO) usada na publicação."""

    async def upload(
        self, object_key: str, data: io.BytesIO, length: int, content_type: str, sha256: str | None
    ) -> None: ...

    async def delete(self, object_key: str) -> None: ...


class MaterialNaoEncontrado(Exception):
    pass


class UnidadeCurricularNaoEncontrada(Exception):
    pass


class TopicoNaoEncontrado(Exception):
    pass


class TopicoForaDaUnidadeCurricular(Exception):
    pass


class FormatoNaoSuportado(Exception):
    pass


class FicheiroVazio(Exception):
    pass


class FicheiroDemasiadoGrande(Exception):
    pass


@dataclass(frozen=True)
class Publicacao:
    material: Material
    versao: VersaoMaterial
    ficheiro: StoredFile
    uc_id: uuid.UUID

@dataclass(frozen=True)
class MaterialListagem:
    material: Material
    versao: VersaoMaterial
    ficheiro: StoredFile
    uc_id: uuid.UUID


async def _validar_associacao(
    session: AsyncSession,
    uc_id: uuid.UUID,
    topico_id: uuid.UUID,
) -> None:
    """Critérios 2 e 3: a UC e o tópico existem e o tópico pertence a essa UC (RN-047)."""
    if await session.get(UnidadeCurricular, uc_id) is None:
        raise UnidadeCurricularNaoEncontrada
    topico = await session.get(Topico, topico_id)
    if topico is None:
        raise TopicoNaoEncontrado
    if topico.uc_id != uc_id:
        raise TopicoForaDaUnidadeCurricular


async def _ler_ficheiro(ficheiro: UploadFile, max_bytes: int) -> tuple[io.BytesIO, int, str]:
    """Lê o ficheiro por partes, sem passar do limite, e calcula o SHA-256 (RN-064)."""
    buffer = io.BytesIO()
    hasher = hashlib.sha256()
    tamanho = 0
    while chunk := await ficheiro.read(CHUNK_SIZE):
        tamanho += len(chunk)
        if tamanho > max_bytes:
            raise FicheiroDemasiadoGrande
        hasher.update(chunk)
        buffer.write(chunk)
    if tamanho == 0:
        raise FicheiroVazio
    buffer.seek(0)
    return buffer, tamanho, hasher.hexdigest()


async def atualizar_material(
    session: AsyncSession,
    material_id: uuid.UUID,
    dados: MaterialUpdate,
) -> MaterialListagem:
    """Atualiza metadados e preserva uma associação académica válida."""
    material = await session.get(Material, material_id)
    if material is None:
        raise MaterialNaoEncontrado

    alteracoes = dados.model_dump(exclude_unset=True)

    topico_atual = await session.get(Topico, material.topico_id)
    if topico_atual is None:
        raise TopicoNaoEncontrado

    novo_topico_id = alteracoes.get("topico_id")
    if novo_topico_id is None:
        novo_topico_id = material.topico_id

    nova_uc_id = alteracoes.get("uc_id")
    if nova_uc_id is None:
        nova_uc_id = topico_atual.uc_id

    await _validar_associacao(session, nova_uc_id, novo_topico_id)

    for campo, valor in alteracoes.items():
        if campo not in {"uc_id", "topico_id"}:
            setattr(material, campo, valor)
    material.topico_id = novo_topico_id

    await session.commit()
    await session.refresh(material)

    versao = await session.scalar(
        select(VersaoMaterial)
        .where(VersaoMaterial.material_id == material.id)
        .order_by(VersaoMaterial.numero.desc())
        .limit(1)
    )
    if versao is None:
        raise RuntimeError("Published material has no version.")

    ficheiro = await session.get(StoredFile, versao.ficheiro_id)
    if ficheiro is None:
        raise RuntimeError("Material version file not found.")

    return MaterialListagem(
        material=material,
        versao=versao,
        ficheiro=ficheiro,
        uc_id=nova_uc_id,
    )


async def publicar_material(
    session: AsyncSession,
    armazenamento: Armazenamento,
    dados: MaterialCreate,
    autor_id: uuid.UUID,
    ficheiro: UploadFile,
    max_bytes: int,
) -> Publicacao:
    """Publica um material da comunidade, sem aprovação prévia (US-022, RN-023)."""
    await _validar_associacao(session, dados.uc_id, dados.topico_id)

    nome = nome_seguro(ficheiro.filename)
    tipo = tipo_do_ficheiro(nome) if nome else None
    if tipo is None:
        raise FormatoNaoSuportado
    conteudo, tamanho, sha256 = await _ler_ficheiro(ficheiro, max_bytes)

    material_id = uuid.uuid4()
    # A chave não usa o nome original, para não depender de caracteres escolhidos pelo utilizador.
    object_key = f"materials/{material_id}/v1/{uuid.uuid4().hex}"
    await armazenamento.upload(object_key, conteudo, tamanho, tipo, sha256)

    try:
        guardado = StoredFile(
            object_key=object_key,
            original_name=nome,
            mime_type=tipo,
            size_bytes=tamanho,
            checksum_sha256=sha256,
        )
        material = Material(
            id=material_id,
            titulo=dados.titulo,
            descricao=dados.descricao,
            categoria=dados.categoria,
            origem=OrigemMaterial.COMUNIDADE,  # Critério 6 (RN-054)
            ano_letivo=dados.ano_letivo,
            topico_id=dados.topico_id,
            autor_id=autor_id,  # Critério 4 (RN-048)
        )
        session.add_all([guardado, material])
        await session.flush()
        versao = VersaoMaterial(material_id=material.id, numero=1, ficheiro_id=guardado.id)
        session.add(versao)
        await session.commit()
    except BaseException:
        # Sem registo na base de dados, o ficheiro no MinIO ficaria órfão.
        await session.rollback()
        try:
            await armazenamento.delete(object_key)
        except Exception:
            logger.exception("Não foi possível apagar o objeto órfão %s", object_key)
        raise

    for objeto in (guardado, material, versao):
        await session.refresh(objeto)
    return Publicacao(material=material, versao=versao, ficheiro=guardado, uc_id=dados.uc_id)


async def listar_materiais_por_topico(
    session: AsyncSession,
    topico_id: uuid.UUID,
) -> list[MaterialListagem]:
    """Lista materiais publicados associados a um tópico (US-021)."""

    topico = await session.get(Topico, topico_id)

    if topico is None:
        raise TopicoNaoEncontrado

    result = await session.scalars(
        select(Material)
        .where(
            Material.topico_id == topico_id,
            Material.estado == EstadoMaterial.PUBLICADO,
        )
        .order_by(Material.publicado_em.desc(), Material.titulo)
    )

    materiais = list(result)
    listagem: list[MaterialListagem] = []

    for material in materiais:
        versao = await session.scalar(
            select(VersaoMaterial)
            .where(VersaoMaterial.material_id == material.id)
            .order_by(VersaoMaterial.numero.desc())
            .limit(1)
        )

        if versao is None:
            logger.error("Material %s sem versão associada.", material.id)
            raise RuntimeError("Published material has no version.")

        ficheiro = await session.get(StoredFile, versao.ficheiro_id)

        if ficheiro is None:
            logger.error("Ficheiro da versão do material %s não encontrado.", material.id)
            raise RuntimeError("Material version file not found.")

        listagem.append(
            MaterialListagem(
                material=material,
                versao=versao,
                ficheiro=ficheiro,
                uc_id=topico.uc_id,
            )
        )

    return listagem
