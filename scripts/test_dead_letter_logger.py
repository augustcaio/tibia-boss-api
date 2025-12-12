"""Script de teste manual para o Dead Letter Logger."""

import asyncio
from pathlib import Path

from app.services.tibiawiki_client import TibiaWikiClient
from app.services.wikitext_parser import ParserError, WikitextParser
from app.utils.dead_letter_logger import dead_letter_logger

# Limpa logs anteriores
dead_letter_logger.clear_logs()


async def test_with_intentional_error():
    """Testa o dead letter logger com erro proposital."""
    print("🧪 Testando Dead Letter Logger com erro proposital...\n")

    # Wikitext inválido (sem template Infobox) - isso causará um erro
    invalid_wikitext = """
    == Description ==
    This is a boss description.
    No Infobox template here.
    This will cause a ParserError.
    """

    try:
        # Tenta fazer parse do wikitext inválido
        boss = WikitextParser.parse(invalid_wikitext, boss_name="Test Boss")
        print("❌ Erro: Parse deveria ter falhado!")
    except ParserError as e:
        print(f"✅ Erro capturado: {e}\n")

        # Loga o erro no dead letter logger
        dead_letter_logger.log_parsing_error(
            boss_name="Test Boss",
            error=e,
            raw_data=invalid_wikitext,
        )

        print("✅ Erro logado no dead letter logger\n")

    # Verifica se o arquivo foi criado
    log_file = Path("logs/parsing_errors.jsonl")
    if log_file.exists():
        print(f"✅ Arquivo de log criado: {log_file}\n")

        # Lê e exibe o conteúdo
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                import json

                entry = json.loads(line)
                print("📋 Conteúdo do log:")
                print(f"  Timestamp: {entry['timestamp']}")
                print(f"  Boss Name: {entry['boss_name']}")
                print(f"  Error Message: {entry['error_message'][:100]}...")
                print(f"  Raw Data Snippet (primeiros 200 chars):")
                print(f"    {entry['raw_data_snippet'][:200]}...")
                print()

        print(f"✅ Total de entradas no log: {dead_letter_logger.get_log_count()}")
    else:
        print("❌ Arquivo de log não foi criado!")


async def test_with_real_boss():
    """Testa com um boss real do TibiaWiki."""
    print("\n🧪 Testando com boss real do TibiaWiki...\n")

    async with TibiaWikiClient() as client:
        # Busca um boss real
        bosses = await client.get_all_bosses()
        if not bosses:
            print("❌ Nenhum boss encontrado")
            return

        test_boss = bosses[0]
        boss_name = test_boss.get("title", "Unknown")
        print(f"📋 Testando com boss: {boss_name}")

        # Busca wikitext
        wikitext = await client.get_boss_wikitext(pageid=test_boss.get("pageid"))

        if wikitext:
            try:
                boss = WikitextParser.parse(wikitext, boss_name=boss_name)
                print(f"✅ Boss parseado com sucesso: {boss.name}")
            except ParserError as e:
                print(f"❌ Erro ao fazer parse: {e}")
                # Loga o erro
                dead_letter_logger.log_parsing_error(
                    boss_name=boss_name,
                    error=e,
                    raw_data=wikitext,
                )
                print("✅ Erro logado no dead letter logger")


if __name__ == "__main__":
    asyncio.run(test_with_intentional_error())
    # asyncio.run(test_with_real_boss())  # Descomente para testar com boss real

