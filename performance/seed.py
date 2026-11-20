"""Insert deterministic synthetic courses into a disposable performance database."""

import asyncio
import ipaddress
import os

from sqlalchemy import select

from backend.app.core.config import settings
from backend.app.core.database import SessionFactory, engine
from backend.app.modules.academic.models import Curso


async def main() -> None:
    if os.getenv("PERF_ENVIRONMENT") != "isolated-local":
        raise RuntimeError("Refusing to seed unless PERF_ENVIRONMENT=isolated-local")
    try:
        local_database = ipaddress.ip_address(settings.postgres_host).is_loopback
    except ValueError:
        local_database = settings.postgres_host == "localhost"
    if not local_database:
        raise RuntimeError("Performance seed is restricted to a local database")

    async with SessionFactory() as session:
        existing = set(
            await session.scalars(select(Curso.codigo).where(Curso.codigo.like("PERF-%")))
        )
        for index in range(1, 101):
            code = f"PERF-{index:04d}"
            if code not in existing:
                session.add(Curso(codigo=code, nome=f"Curso sintético {index:04d}"))
        await session.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
