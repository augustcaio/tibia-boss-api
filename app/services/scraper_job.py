"""Job de scraping de bosses utilizado pelo scheduler e endpoint admin.

Este job reutiliza a pipeline definida em app.main_scraper, mas respeita
um lock distribuído em MongoDB (system_jobs.scraper_lock) para evitar
execuções concorrentes.
"""

import asyncio
import logging

from app.core.database import get_database
from app.db.repository import BossRepository
from app.db.system_jobs import SystemJobsRepository
from app.main_scraper import (
    BATCH_SIZE,
    MAX_CONCURRENT_REQUESTS,
    process_and_save_batch,
    process_batch_with_images,
    process_boss,
)
from app.services.image_resolver import ImageResolverService
from app.services.tibiawiki_client import TibiaWikiClient
from app.utils.dead_letter_logger import dead_letter_logger

logger = logging.getLogger(__name__)


async def run_scraper_job() -> None:
    """
    Executa o job de scraping completo respeitando o Mongo Mutex.

    - Garante a existência do documento de lock
    - Tenta adquirir o lock (status: idle -> running)
    - Se não conseguir, aborta silenciosamente
    - Em caso de sucesso, executa a pipeline de scraping
    - No finally, libera o lock (status: running -> idle, atualiza last_run)
    """
    db = get_database()
    system_jobs_repo = SystemJobsRepository(db)

    # Garante documento base do lock
    await system_jobs_repo.ensure_scraper_lock_document()

    # Tenta adquirir o lock
    if not await system_jobs_repo.acquire_scraper_lock():
        logger.info("Job already running - abortando nova execução do scraper")
        return

    try:
        logger.info("=" * 60)
        logger.info("Iniciando job de sincronização de Bosses (Scheduler/Admin)")
        logger.info("=" * 60)

        repository = BossRepository(db)

        # Cria semáforo para limitar requisições simultâneas
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

        async with TibiaWikiClient() as client, ImageResolverService() as image_resolver:
            # 1. Busca lista de todos os bosses
            logger.info("Buscando lista de todos os bosses...")
            bosses_list = await client.get_all_bosses()
            total_bosses = len(bosses_list)
            logger.info(f"Total de bosses encontrados: {total_bosses}")

            # 2. Processa cada boss em paralelo (limitado pelo semáforo)
            logger.info(
                "Processando bosses (máx %s simultâneos)...",
                MAX_CONCURRENT_REQUESTS,
            )
            logger.info("-" * 60)

            tasks = [process_boss(client, boss_info, semaphore) for boss_info in bosses_list]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filtra resultados válidos (remove None e exceções)
            processed_bosses = []
            for result in results:
                from app.models.boss import BossModel  # import local para evitar ciclos

                if isinstance(result, BossModel):
                    processed_bosses.append(result)
                elif isinstance(result, Exception):
                    logger.error("Exceção não tratada: %s", result)
                    dead_letter_logger.log_parsing_error(
                        boss_name="unknown",
                        error=result,
                        raw_data=None,
                    )

            success_count = len(processed_bosses)
            failure_count = total_bosses - success_count
            success_rate = (success_count / total_bosses * 100) if total_bosses > 0 else 0

            logger.info("-" * 60)
            logger.info("Parse concluído:")
            logger.info("  Total: %s", total_bosses)
            logger.info("  Sucesso: %s", success_count)
            logger.info("  Falhas: %s", failure_count)
            logger.info("  Taxa de sucesso: %.1f%%", success_rate)

            # 3. Processa em lotes: resolve imagens e salva no MongoDB
            logger.info("-" * 60)
            logger.info("Processando em lotes de %s bosses...", BATCH_SIZE)

            total_saved = 0
            for i in range(0, len(processed_bosses), BATCH_SIZE):
                batch = processed_bosses[i : i + BATCH_SIZE]
                batch_num = (i // BATCH_SIZE) + 1
                total_batches = (len(processed_bosses) + BATCH_SIZE - 1) // BATCH_SIZE

                logger.info(
                    "Processando lote %s/%s (%s bosses)...",
                    batch_num,
                    total_batches,
                    len(batch),
                )

                # Reutiliza a função de main_scraper para enriquecer e salvar
                saved = await process_and_save_batch(
                    batch,
                    image_resolver=image_resolver,
                    repository=repository,
                )
                total_saved += saved

            logger.info("-" * 60)
            logger.info("✅ Job de sincronização completo:")
            logger.info("  Bosses processados: %s", success_count)
            logger.info("  Bosses salvos no MongoDB: %s", total_saved)
            logger.info("=" * 60)

            if success_rate >= 90:
                logger.info("✅ DoD: Taxa de sucesso >= 90%%")
            else:
                logger.warning("⚠️ DoD: Taxa de sucesso %.1f%% < 90%%", success_rate)

    except Exception as exc:  # noqa: BLE001
        logger.exception("Erro ao executar job de sincronização: %s", exc)
    finally:
        # Garante liberação do lock mesmo em caso de erro
        await system_jobs_repo.release_scraper_lock()
