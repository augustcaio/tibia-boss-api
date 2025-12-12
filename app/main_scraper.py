"""Script orchestrator para extrair e processar dados de Bosses do TibiaWiki.

Este script integra o TibiaWikiClient e o WikitextParser para:
1. Buscar lista de todos os bosses
2. Processar cada boss (buscar wikitext e fazer parse)
3. Salvar resultado em JSON
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from app.models.boss import BossModel
from app.services.tibiawiki_client import TibiaWikiClient
from app.services.wikitext_parser import ParserError, WikitextParser

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# Configurações
MAX_CONCURRENT_REQUESTS = 10
OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "bosses_dump.json"


async def process_boss(
    client: TibiaWikiClient,
    boss_info: Dict,
    semaphore: asyncio.Semaphore,
) -> Optional[BossModel]:
    """
    Processa um único boss: busca wikitext e faz parse.

    Args:
        client: Instância do TibiaWikiClient
        boss_info: Dicionário com informações do boss (pageid, title)
        semaphore: Semáforo para limitar requisições simultâneas

    Returns:
        BossModel se processado com sucesso, None caso contrário
    """
    boss_name = boss_info.get("title", "Unknown")
    pageid = boss_info.get("pageid")

    async with semaphore:
        try:
            # Busca o wikitext do boss
            wikitext = await client.get_boss_wikitext(pageid=pageid)

            if not wikitext:
                logger.warning(f"Wikitext não encontrado para: {boss_name}")
                return None

            # Faz o parse do wikitext
            boss_model = WikitextParser.parse(wikitext, boss_name=boss_name)

            logger.info(f"Processed {boss_name}")
            return boss_model

        except ParserError as e:
            logger.error(f"Failed parsing {boss_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing {boss_name}: {e}")
            return None


async def main():
    """Função principal do script orchestrator."""
    logger.info("=" * 60)
    logger.info("Iniciando scraper de Bosses do TibiaWiki")
    logger.info("=" * 60)

    # Cria diretório de saída se não existir
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Cria semáforo para limitar requisições simultâneas
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async with TibiaWikiClient() as client:
        # 1. Busca lista de todos os bosses
        logger.info("Buscando lista de todos os bosses...")
        bosses_list = await client.get_all_bosses()
        total_bosses = len(bosses_list)
        logger.info(f"Total de bosses encontrados: {total_bosses}")

        # 2. Processa cada boss em paralelo (limitado pelo semáforo)
        logger.info(f"Processando bosses (máx {MAX_CONCURRENT_REQUESTS} simultâneos)...")
        logger.info("-" * 60)

        tasks = [
            process_boss(client, boss_info, semaphore) for boss_info in bosses_list
        ]

        # Usa gather para processar em paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filtra resultados válidos (remove None e exceções)
        processed_bosses: List[BossModel] = []
        for result in results:
            if isinstance(result, BossModel):
                processed_bosses.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Exceção não tratada: {result}")

        success_count = len(processed_bosses)
        failure_count = total_bosses - success_count
        success_rate = (success_count / total_bosses * 100) if total_bosses > 0 else 0

        logger.info("-" * 60)
        logger.info(f"Processamento concluído:")
        logger.info(f"  Total: {total_bosses}")
        logger.info(f"  Sucesso: {success_count}")
        logger.info(f"  Falhas: {failure_count}")
        logger.info(f"  Taxa de sucesso: {success_rate:.1f}%")

        # 3. Salva resultado em JSON
        logger.info(f"Salvando resultados em {OUTPUT_FILE}...")

        # Converte BossModel para dict
        bosses_data = [boss.model_dump() for boss in processed_bosses]

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(bosses_data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ {len(bosses_data)} bosses salvos em {OUTPUT_FILE}")
        logger.info("=" * 60)

        # Validação do DoD
        if success_rate >= 90:
            logger.info("✅ DoD: Taxa de sucesso >= 90%")
        else:
            logger.warning(f"⚠️  DoD: Taxa de sucesso {success_rate:.1f}% < 90%")


if __name__ == "__main__":
    asyncio.run(main())

