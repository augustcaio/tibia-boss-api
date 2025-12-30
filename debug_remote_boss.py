import asyncio
import logging

from app.services.tibiawiki_client import TibiaWikiClient
from app.services.wikitext_parser import WikitextParser

logging.basicConfig(level=logging.INFO)

async def debug_boss(name):
    async with TibiaWikiClient() as client:
        print(f"🔍 Fetching wikitext for {name}...")
        try:
            # Try to get by title
            wikitext = await client.get_boss_wikitext(title=name)
            if not wikitext:
                print(f"❌ Wikitext not found for {name}")
                return

            print(f"📄 Wikitext length: {len(wikitext)}")
            print("-" * 40)
            # Print first 500 chars
            print(wikitext[:500])
            print("-" * 40)

            boss = WikitextParser.parse(wikitext, boss_name=name)
            print(f"✅ Parsed boss: {boss.name}")
            print(f"   HP: {boss.hp}")
            print(f"   Visuals: {boss.visuals}")
            
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(debug_boss("Abyssador"))

