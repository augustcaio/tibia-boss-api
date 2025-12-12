"""Script orchestrator para extrair e processar dados de Bosses do TibiaWiki.

Este script integra:
1. TibiaWikiClient - busca lista de bosses e wikitext
2. WikitextParser - extrai dados estruturados + nome do arquivo de imagem
3. ImageResolverService - resolve URLs de imagens em lote
4. BossRepository - persiste dados no MongoDB
"""

import asyncio
import logging
from typing import Dict, List, Optional

from app.core.config import settings
from app.db.connection import close_database, init_database
from app.db.repository import BossRepository
from app.models.boss import BossModel, BossVisuals
from app.services.image_resolver import ImageResolverService
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
BATCH_SIZE = 50  # Tamanho do lote para processamento de imagens e salvamento


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

            # Faz o parse do wikitext (já extrai image_filename se disponível)
            boss_model = WikitextParser.parse(wikitext, boss_name=boss_name)

            logger.debug(f"Processed {boss_name}")
            return boss_model

        except ParserError as e:
            logger.error(f"Failed parsing {boss_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing {boss_name}: {e}")
            return None


async def process_batch_with_images(
    bosses: List[BossModel],
    image_resolver: ImageResolverService,
) -> List[BossModel]:
    """
    Processa um lote de bosses resolvendo URLs de imagens.

    Args:
        bosses: Lista de BossModel com filename já extraído
        image_resolver: Instância do ImageResolverService

    Returns:
        Lista de bosses enriquecidos com URLs de imagens
    """
    if not bosses:
        return []

    # Coleta todos os filenames de imagens do lote
    image_filenames = []
    boss_to_filenames = {}  # Mapeia boss -> filename para atualizar depois

    for boss in bosses:
        if boss.visuals and boss.visuals.filename:
            filename = boss.visuals.filename
            image_filenames.append(filename)
            boss_to_filenames[boss] = filename

    # Se não há imagens, retorna os bosses sem modificação
    if not image_filenames:
        logger.debug(f"Nenhuma imagem encontrada no lote de {len(bosses)} bosses")
        return bosses

    # Remove duplicatas mantendo ordem
    unique_filenames = list(dict.fromkeys(image_filenames))

    logger.info(f"Resolvendo {len(unique_filenames)} imagens para lote de {len(bosses)} bosses...")

    # Resolve URLs das imagens em lote
    try:
        image_urls = await image_resolver.resolve_images(unique_filenames)
    except Exception as e:
        logger.error(f"Erro ao resolver imagens: {e}")
        image_urls = {}

    # Enriquece os bosses com as URLs resolvidas
    enriched_bosses = []
    for boss in bosses:
        if boss in boss_to_filenames:
            filename = boss_to_filenames[boss]
            url = image_urls.get(filename)

            # Atualiza ou cria o objeto visuals
            if boss.visuals:
                boss.visuals.gif_url = url
            else:
                boss.visuals = BossVisuals(filename=filename, gif_url=url)

        enriched_bosses.append(boss)

    return enriched_bosses


async def process_and_save_batch(
    bosses: List[BossModel],
    image_resolver: ImageResolverService,
    repository: BossRepository,
) -> int:
    """
    Processa um lote de bosses: resolve imagens e salva no MongoDB.

    Args:
        bosses: Lista de BossModel
        image_resolver: Instância do ImageResolverService
        repository: Instância do BossRepository

    Returns:
        Número de bosses salvos com sucesso
    """
    if not bosses:
        return 0

    # Resolve URLs de imagens
    enriched_bosses = await process_batch_with_images(bosses, image_resolver)

    # Salva no MongoDB
    success_count = await repository.upsert_batch(enriched_bosses)

    logger.info(f"Lote processado: {success_count}/{len(enriched_bosses)} bosses salvos")
    return success_count


async def main():
    """Função principal do script orchestrator."""
    logger.info("=" * 60)
    logger.info("Iniciando scraper de Bosses do TibiaWiki (Sprint 2)")
    logger.info("=" * 60)

    # Inicializa MongoDB
    logger.info("Inicializando conexão MongoDB...")
    db = await init_database(
        mongodb_url=settings.mongodb_url,
        database_name=settings.database_name,
    )
    repository = BossRepository(db)
    logger.info("✅ MongoDB conectado e índices criados")

    # Cria semáforo para limitar requisições simultâneas
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async with TibiaWikiClient() as client, ImageResolverService() as image_resolver:
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
        logger.info(f"Parse concluído:")
        logger.info(f"  Total: {total_bosses}")
        logger.info(f"  Sucesso: {success_count}")
        logger.info(f"  Falhas: {failure_count}")
        logger.info(f"  Taxa de sucesso: {success_rate:.1f}%")

        # 3. Processa em lotes: resolve imagens e salva no MongoDB
        logger.info("-" * 60)
        logger.info(f"Processando em lotes de {BATCH_SIZE} bosses...")

        total_saved = 0
        for i in range(0, len(processed_bosses), BATCH_SIZE):
            batch = processed_bosses[i : i + BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            total_batches = (len(processed_bosses) + BATCH_SIZE - 1) // BATCH_SIZE

            logger.info(f"Processando lote {batch_num}/{total_batches} ({len(batch)} bosses)...")

            saved = await process_and_save_batch(batch, image_resolver, repository)
            total_saved += saved

        logger.info("-" * 60)
        logger.info(f"✅ Pipeline completo:")
        logger.info(f"  Bosses processados: {success_count}")
        logger.info(f"  Bosses salvos no MongoDB: {total_saved}")
        logger.info("=" * 60)

        # Validação do DoD
        if success_rate >= 90:
            logger.info("✅ DoD: Taxa de sucesso >= 90%")
        else:
            logger.warning(f"⚠️  DoD: Taxa de sucesso {success_rate:.1f}% < 90%")

    # Fecha conexão MongoDB
    await close_database()
    logger.info("Conexão MongoDB fechada")


if __name__ == "__main__":
    asyncio.run(main())
