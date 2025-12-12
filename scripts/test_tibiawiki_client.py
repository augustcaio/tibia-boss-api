"""Script de teste manual para TibiaWikiClient.

Este script testa a comunicação real com a API do TibiaWiki
e imprime uma lista de nomes de Bosses no console.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para importar app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.tibiawiki_client import TibiaWikiClient

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def main():
    """Função principal do script de teste."""
    logger.info("Iniciando teste do TibiaWikiClient...")

    async with TibiaWikiClient() as client:
        try:
            # Teste 1: Buscar todos os bosses
            logger.info("Buscando lista de todos os bosses...")
            bosses = await client.get_all_bosses()

            logger.info(f"\n✅ Total de bosses encontrados: {len(bosses)}\n")
            logger.info("=" * 60)
            logger.info("LISTA DE BOSSES:")
            logger.info("=" * 60)

            # Imprime os primeiros 20 bosses como exemplo
            for i, boss in enumerate(bosses[:20], 1):
                logger.info(f"{i:3d}. {boss.get('title', 'N/A')} (ID: {boss.get('pageid', 'N/A')})")

            if len(bosses) > 20:
                logger.info(f"\n... e mais {len(bosses) - 20} bosses")

            # Teste 2: Buscar wikitext de um boss específico
            if bosses:
                first_boss = bosses[0]
                logger.info(f"\n{'=' * 60}")
                logger.info(f"Testando extração de wikitext para: {first_boss.get('title')}")
                logger.info("=" * 60)

                wikitext = await client.get_boss_wikitext(
                    pageid=first_boss.get("pageid")
                )

                if wikitext:
                    preview = wikitext[:200] + "..." if len(wikitext) > 200 else wikitext
                    logger.info(f"\n✅ Wikitext obtido com sucesso!")
                    logger.info(f"Preview (primeiros 200 chars):\n{preview}")
                else:
                    logger.warning(f"\n⚠️  Não foi possível obter wikitext para {first_boss.get('title')}")

            logger.info("\n" + "=" * 60)
            logger.info("✅ Teste concluído com sucesso!")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ Erro durante o teste: {e}", exc_info=True)
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

