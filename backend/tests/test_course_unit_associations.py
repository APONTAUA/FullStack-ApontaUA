"""Testes das associações entre cursos e unidades curriculares (US-017)."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.app.modules.academic.models import Curso, UnidadeCurricular


async def test_associa_unidade_curricular_a_curso(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        curso = Curso(codigo="LEI", nome="Engenharia Informática")
        session.add(curso)
        await session.flush()

        uc = UnidadeCurricular(
            codigo="CD",
            nome="Computação Distribuída",
            curso_id=curso.id,
        )
        session.add(uc)
        await session.commit()

        resultado = await session.scalar(
            select(UnidadeCurricular).where(UnidadeCurricular.codigo == "CD")
        )

        assert resultado is not None
        assert resultado.curso_id == curso.id


async def test_rejeita_associacao_a_curso_inexistente(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        uc = UnidadeCurricular(
            codigo="SIO",
            nome="Segurança Informática",
            curso_id=uuid.uuid4(),
        )
        session.add(uc)

        with pytest.raises(IntegrityError):
            await session.commit()


async def test_unidade_curricular_sem_curso(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        uc = UnidadeCurricular(
            codigo="TQS",
            nome="Teste e Qualidade de Software",
        )
        session.add(uc)
        await session.commit()

        assert uc.curso_id is None