"""Verificação provisória de papéis.

A autenticação institucional (EPIC-01) e a gestão de papéis (EPIC-02) ainda não existem.
Até lá, o papel é indicado no cabeçalho `X-Dev-Role`, apenas para desenvolvimento local.
O cabeçalho só é aceite quando `APP_ENV` está definido explicitamente como `development`
ou `test`. Se `APP_ENV` faltar (o valor por omissão em `config.py` é `development`) ou
tiver outro valor, todos os pedidos são recusados, para que um deploy mal configurado
não deixe as rotas protegidas abertas.

Quando a autenticação existir, basta substituir `get_current_role` pela leitura do
utilizador autenticado e dos seus papéis; as rotas continuam a usar as mesmas dependências.
"""

from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from backend.app.core.config import Settings, settings


class Papel(StrEnum):
    ESTUDANTE = "estudante"
    DOCENTE = "docente"
    REPRESENTANTE = "representante"
    MODERADOR = "moderador"
    ADMINISTRADOR = "administrador"


DEV_ROLE_HEADER = "X-Dev-Role"


def dev_roles_enabled(current: Settings) -> bool:
    """O papel simulado só vale com APP_ENV explícito e de desenvolvimento ou teste."""
    return "app_env" in current.model_fields_set and current.app_env in {"development", "test"}


async def get_current_role(
    x_dev_role: Annotated[str | None, Header(alias=DEV_ROLE_HEADER)] = None,
) -> Papel:
    if not dev_roles_enabled(settings):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is not configured yet.",
        )
    if x_dev_role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing {DEV_ROLE_HEADER} header (development only).",
        )
    try:
        return Papel(x_dev_role.strip().lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unknown role in {DEV_ROLE_HEADER} header.",
        ) from None


CurrentRole = Annotated[Papel, Depends(get_current_role)]


def require_roles(*allowed: Papel) -> Callable[[Papel], Awaitable[Papel]]:
    async def dependency(role: CurrentRole) -> Papel:
        if role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return role

    return dependency
