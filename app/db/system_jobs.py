"""Repositório para controle de jobs de sistema (Mongo Mutex para o scraper)."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

logger = logging.getLogger(__name__)


@dataclass
class ScraperLockStatus:
    """Representa o estado atual do lock do scraper."""

    status: str
    last_run: datetime | None
    locked_at: datetime | None


class SystemJobsRepository:
    """Repositório para a coleção system_jobs (locks de jobs)."""

    SCRAPER_LOCK_ID = "scraper_lock"

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = database.system_jobs

    async def ensure_scraper_lock_document(self) -> None:
        """
        Garante que o documento base do lock do scraper exista.

        Se não existir, cria com status 'idle'.
        """
        await self.collection.update_one(
            {"_id": self.SCRAPER_LOCK_ID},
            {
                "$setOnInsert": {
                    "status": "idle",
                    "last_run": None,
                    "locked_at": None,
                }
            },
            upsert=True,
        )

    async def acquire_scraper_lock(self) -> bool:
        """
        Tenta adquirir o lock do scraper.

        Returns:
            True se o lock foi adquirido com sucesso, False se já existe um job rodando.
        """
        now = datetime.now(UTC)

        result = await self.collection.find_one_and_update(
            {"_id": self.SCRAPER_LOCK_ID, "status": "idle"},
            {"$set": {"status": "running", "locked_at": now}},
            return_document=ReturnDocument.AFTER,
        )

        if result is None:
            logger.info("Job already running - não foi possível adquirir o lock")
            return False

        logger.info("Lock acquired para o job de scraper")
        return True

    async def release_scraper_lock(self) -> None:
        """Libera o lock do scraper, marcando o job como idle e atualizando last_run."""
        now = datetime.now(UTC)

        result = await self.collection.update_one(
            {"_id": self.SCRAPER_LOCK_ID},
            {
                "$set": {
                    "status": "idle",
                    "last_run": now,
                    "locked_at": None,
                }
            },
        )

        if result.matched_count == 0:
            logger.warning(
                "Tentativa de liberar lock do scraper, mas documento não foi encontrado",
            )
        else:
            logger.info("Lock liberado para o job de scraper")
