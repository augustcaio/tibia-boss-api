import asyncio
import sys
import json
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.tibiawiki_client import TibiaWikiClient
from app.services.wikitext_parser import WikitextParser

async def test_abyssador_extraction():
    async with TibiaWikiClient() as client:
        print("Finding Abyssador...")
        # Get Abyssador wikitext
        wikitext = await client.get_boss_wikitext(title="Abyssador")
        
        if not wikitext:
            print("Could not find Abyssador wikitext")
            return

        print("Parsing wikitext...")
        boss = WikitextParser.parse(wikitext, boss_name="Abyssador")
        
        print("\n=== EXTRACTED DATA (ABYSSADOR) ===")
        print(f"Name:    {boss.name}")
        print(f"HP:      {boss.hp}")
        print(f"EXP:     {boss.exp}")
        print(f"Speed:   {boss.speed}")
        print(f"Version: {boss.version}")
        print(f"Loot:       {boss.loot}")
        print(f"Abilities:  {boss.abilities}")
        print(f"Sounds:     {boss.sounds}")
        print(f"Resistances (Detailed):")
        for k, v in boss.resistances.items():
            print(f"  - {k}: {v}%")
        
        # Verify specific values from the user report
        print("\n=== VERIFICATION ===")
        if boss.hp == 340000:
            print("✅ HP matches (340,000)")
        else:
            print(f"❌ HP mismatch: {boss.hp}")
            
        if boss.exp == 400000:
            print("✅ EXP matches (400,000)")
        else:
            print(f"❌ EXP mismatch: {boss.exp}")

        if boss.resistances.get("earth") == 0:
            print("✅ Earth Resistance matches (0%)")
        else:
            print(f"❌ Earth Resistance mismatch: {boss.resistances.get('earth')}")

        if boss.resistances.get("fire") == 85:
            print("✅ Fire Resistance matches (85%)")
        else:
            print(f"❌ Fire Resistance mismatch: {boss.resistances.get('fire')}")

if __name__ == "__main__":
    asyncio.run(test_abyssador_extraction())
