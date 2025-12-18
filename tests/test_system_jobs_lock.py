"""Testes para o lock distribuído em system_jobs."""

import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.connection import close_database, init_database
from app.db.system_jobs import SystemJobsRepository


@pytest.fixture
async def test_database():
    """Cria um banco de dados de teste isolado para system_jobs."""
    db = await init_database(
        mongodb_url="mongodb://localhost:27017",
        database_name="tibia_bosses_lock_test",
    )
    yield db

    await db.client.drop_database("tibia_bosses_lock_test")
    await close_database()


@pytest.mark.asyncio
async def test_acquire_and_release_lock(test_database: AsyncIOMotorDatabase):
    """Garante que o lock do scraper respeita acquire/release corretamente."""
    repo = SystemJobsRepository(test_database)

    # Garante documento base
    await repo.ensure_scraper_lock_document()

    # Primeiro acquire deve funcionar
    first = await repo.acquire_scraper_lock()
    assert first is True

    # Segundo acquire sem release deve falhar
    second = await repo.acquire_scraper_lock()
    assert second is False

    # Release libera o lock
    await repo.release_scraper_lock()

    # Novo acquire deve voltar a funcionar
    third = await repo.acquire_scraper_lock()
    assert third is True


