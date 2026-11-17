"""Testes do modelo UnidadeCurricular (US-016)."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from backend.app.modules.academic.models import UnidadeCurricular


async def test_cria_unidade_curricular_valida(session_factory):
    """Confirma que uma UC válida é guardada na base de dados."""
    async with session_factory() as session:
        uc = UnidadeCurricular(
            codigo="40337",
            nome="PEI",
        )

        session.add(uc)
        await session.commit()

        assert isinstance(uc.id, uuid.UUID)

        resultado = await session.scalar(
            select(UnidadeCurricular).where(UnidadeCurricular.codigo == "40337")
        )

        assert resultado is not None
        assert resultado.id == uc.id
        assert resultado.codigo == "40337"
        assert resultado.nome == "PEI"


async def test_rejeita_codigo_duplicado(session_factory):
    """Não permite duas UCs com o mesmo código."""
    async with session_factory() as session:
        session.add(
            UnidadeCurricular(
                codigo="40337",
                nome="PEI",
            )
        )
        await session.commit()

        session.add(
            UnidadeCurricular(
                codigo="40337",
                nome="Outra UC",
            )
        )

        with pytest.raises(IntegrityError):
            await session.commit()

        await session.rollback()


async def test_rejeita_uc_sem_codigo(session_factory):
    """Não permite criar uma UC sem código."""
    async with session_factory() as session:
        session.add(UnidadeCurricular(nome="PEI"))

        with pytest.raises(IntegrityError):
            await session.commit()

        await session.rollback()


async def test_rejeita_uc_sem_nome(session_factory):
    """Não permite criar uma UC sem nome."""
    async with session_factory() as session:
        session.add(UnidadeCurricular(codigo="40337"))

        with pytest.raises(IntegrityError):
            await session.commit()

        await session.rollback()
