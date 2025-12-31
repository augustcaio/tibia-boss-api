import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.wikitext_parser import WikitextParser

def test_parsing_logic():
    wikitext = """
{{Infobox Boss
| name             = Abyssador
| image            = Abyssador.gif
| hp               = 340,000
| exp              = 400,000
| speed            = 230
| implemented      = 9.60
| physical         = 100
| earth            = 0
| energy           = 85
| ice              = 85
| fire             = 85
| death            = 85
| holy             = 100
| drown            = 100
| walks_through     = Fire, Energy, Poison
| abilities        = Melee (0-1400), Earth Wave (500-1100), Stone Shower Beam (500-1200), Stealth, Massive Heal
| sounds           = BRAINS SMALL, DEATH, EXISTENCE FUTILE
| location         = [[Warzone 3]]
| loot             = [[Abyssador's Lash]], [[Shiny Blade]], [[Mycological Bow]], [[Crystalline Axe]]
}}
"""
    print("Parsing hardcoded Abyssador wikitext...")
    try:
        boss = WikitextParser.parse(wikitext, boss_name="Abyssador")
        
        print("\n=== EXTRACTED DATA ===")
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
            
        errors = []
        if boss.hp != 340000: errors.append(f"HP {boss.hp} != 340000")
        if boss.exp != 400000: errors.append(f"EXP {boss.exp} != 400000")
        if boss.speed != 230: errors.append(f"Speed {boss.speed} != 230")
        if boss.version != "9.60": errors.append(f"Version {boss.version} != 9.60")
        if "Abyssador's Lash" not in boss.loot[0]: errors.append("Loot missing Abyssador's Lash")
        if boss.resistances.get("earth") != 0: errors.append("Earth resistance != 0")
        if boss.resistances.get("fire") != 85: errors.append("Fire resistance != 85")
        
        if not errors:
            print("\n✅ ALL TESTS PASSED!")
        else:
            print("\n❌ TESTS FAILED:")
            for e in errors:
                print(f"  - {e}")
                
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parsing_logic()
