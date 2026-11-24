import hashlib
import io
import logging
import uuid
from dataclasses import dataclass
from typing import Protocol

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.academic.models import UnidadeCurricular
from backend.app.modules.academic.topicos.models import Topico
from backend.app.modules.materials.formats import nome_seguro, tipo_do_ficheiro
from backend.app.modules.materials.models import Material, OrigemMaterial, VersaoMaterial
from backend.app.modules.materials.schemas import MaterialCreate
from backend.app.modules.storage.models import StoredFile

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 1024


class Armazenamento(Protocol):
    """Parte do ObjectStorage (MinIO) usada na publicação."""

    async def upload(
        self, object_key: str, data: io.BytesIO, length: int, content_type: str, sha256: str | None
    ) -> None: ...

    async def delete(self, object_key: str) -> None: ...


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


async def _validar_associacao(session: AsyncSession, dados: MaterialCreate) -> None:
    """Critérios 2 e 3: a UC e o tópico existem e o tópico pertence a essa UC (RN-047)."""
    if await session.get(UnidadeCurricular, dados.uc_id) is None:
        raise UnidadeCurricularNaoEncontrada
    topico = await session.get(Topico, dados.topico_id)
    if topico is None:
        raise TopicoNaoEncontrado
    if topico.uc_id != dados.uc_id:
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


async def publicar_material(
    session: AsyncSession,
    armazenamento: Armazenamento,
    dados: MaterialCreate,
    autor_id: uuid.UUID,
    ficheiro: UploadFile,
    max_bytes: int,
) -> Publicacao:
    """Publica um material da comunidade, sem aprovação prévia (US-022, RN-023)."""
    await _validar_associacao(session, dados)

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
