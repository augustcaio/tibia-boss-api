"""Script de teste rápido para validar o main_scraper com poucos bosses."""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main_scraper import process_boss
from app.services.tibiawiki_client import TibiaWikiClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def test_with_few_bosses():
    """Testa o scraper com apenas os primeiros 5 bosses."""
    logger.info("Testando scraper com primeiros 5 bosses...")

    semaphore = asyncio.Semaphore(10)

    async with TibiaWikiClient() as client:
        # Busca lista de bosses
        bosses_list = await client.get_all_bosses()
        test_bosses = bosses_list[:5]  # Apenas os primeiros 5

        logger.info(f"Testando com {len(test_bosses)} bosses...")

        # Processa
        tasks = [
            process_boss(client, boss_info, semaphore) for boss_info in test_bosses
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Mostra resultados
        success = sum(1 for r in results if r is not None and not isinstance(r, Exception))
        logger.info(f"Sucesso: {success}/{len(test_bosses)}")

        # Mostra alguns resultados
        for result in results:
            if result and not isinstance(result, Exception):
                logger.info(f"  ✅ {result.name}: HP={result.hp}, EXP={result.exp}")


if __name__ == "__main__":
    asyncio.run(test_with_few_bosses())

