"""Formatos aceites no MVP (RN-046, RF-028).

Validação básica pela extensão do nome do ficheiro. O tipo MIME guardado é o da extensão e não o
que o browser indica. A verificação do conteúdo real do ficheiro fica para a US-024.
"""

from pathlib import PurePath

TIPOS_POR_EXTENSAO: dict[str, str] = {
    ".pdf": "application/pdf",
    ".md": "text/markdown",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}

NOME_MAX_LENGTH = 255


def nome_seguro(nome_original: str | None) -> str:
    """Só o nome do ficheiro, sem pastas, e com o tamanho que cabe na base de dados."""
    nome = PurePath((nome_original or "").replace("\\", "/")).name.strip()
    if len(nome) <= NOME_MAX_LENGTH:
        return nome
    sufixo = PurePath(nome).suffix[:20]
    return nome[: NOME_MAX_LENGTH - len(sufixo)] + sufixo


def tipo_do_ficheiro(nome: str) -> str | None:
    """Tipo MIME para um nome de ficheiro aceite, ou None se o formato não for suportado."""
    return TIPOS_POR_EXTENSAO.get(PurePath(nome).suffix.lower())
