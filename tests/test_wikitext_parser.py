"""Testes unitários para WikitextParser."""

import pytest

from app.models.boss import BossModel
from app.services.wikitext_parser import ParserError, WikitextParser


def test_parse_simple_boss():
    """Testa parsing de um boss simples."""
    wikitext = """
    {{Infobox Boss
    |name = Test Boss
    |hp = 50000
    |exp = 10000
    |walks_through = Fire
    |immunities = Energy
    }}
    """

    boss = WikitextParser.parse(wikitext, "Test Boss")

    assert isinstance(boss, BossModel)
    assert boss.name == "Test Boss"
    assert boss.hp == 50000
    assert boss.exp == 10000
    assert "Fire" in boss.walks_through
    assert "Energy" in boss.immunities


def test_parse_boss_with_complex_hp():
    """Testa parsing de boss com HP complexo."""
    wikitext = """
    {{Infobox Boss
    |name = Complex Boss
    |hp = 50,000 (estimated)
    |exp = 10,000
    }}
    """

    boss = WikitextParser.parse(wikitext, "Complex Boss")

    assert boss.hp == 50000
    assert boss.exp == 10000


def test_parse_boss_with_unknown_hp():
    """Testa parsing de boss sem HP."""
    wikitext = """
    {{Infobox Boss
    |name = Unknown HP Boss
    |hp = ???
    |exp = 10000
    }}
    """

    boss = WikitextParser.parse(wikitext, "Unknown HP Boss")

    assert boss.hp is None
    assert boss.exp == 10000


def test_parse_boss_with_variable_hp():
    """Testa parsing de boss com HP variável."""
    wikitext = """
    {{Infobox Boss
    |name = Variable Boss
    |hp = Variable
    }}
    """

    boss = WikitextParser.parse(wikitext, "Variable Boss")

    assert boss.hp is None


def test_parse_boss_with_immunities_list():
    """Testa parsing de boss com múltiplas immunities."""
    wikitext = """
    {{Infobox Boss
    |name = Immune Boss
    |immunities = Fire, Energy (partial)
    }}
    """

    boss = WikitextParser.parse(wikitext, "Immune Boss")

    assert "Fire" in boss.immunities
    assert "Energy" in boss.immunities
    assert len(boss.immunities) == 2


def test_parse_boss_without_infobox():
    """Testa parsing de wikitext sem Infobox Boss."""
    wikitext = """
    Este é um texto qualquer sem template.
    """

    with pytest.raises(ParserError, match="Template 'Infobox Boss' ou 'Infobox Creature' não encontrado"):
        WikitextParser.parse(wikitext, "Test Boss")


def test_parse_empty_wikitext():
    """Testa parsing de wikitext vazio."""
    with pytest.raises(ParserError, match="Wikitext vazio"):
        WikitextParser.parse("", "Test Boss")


def test_parse_boss_old_format():
    """Testa parsing de boss com formato antigo."""
    wikitext = """
    {{Infobox Boss
    |hitpoints = 50000
    |experience = 10000
    }}
    """

    boss = WikitextParser.parse(wikitext, "Old Format Boss")

    assert boss.hp == 50000
    assert boss.exp == 10000


def test_parse_boss_new_format():
    """Testa parsing de boss com formato novo."""
    wikitext = """
    {{Infobox Boss
    |hp = 50000
    |exp = 10000
    }}
    """

    boss = WikitextParser.parse(wikitext, "New Format Boss")

    assert boss.hp == 50000
    assert boss.exp == 10000


def test_parse_boss_with_broken_formatting():
    """Testa parsing de boss com formatação quebrada."""
    wikitext = """
    {{Infobox Boss
    |hp = 50,000 (estimated) (maybe)
    |exp = ???
    |walks_through = Fire, Energy, Ice (all partial)
    }}
    """

    boss = WikitextParser.parse(wikitext, "Broken Format Boss")

    # Deve conseguir extrair o HP mesmo com formatação quebrada
    assert boss.hp == 50000
    assert boss.exp is None
    assert len(boss.walks_through) >= 2


def test_parse_boss_name_from_template():
    """Testa que o nome pode ser extraído do template."""
    wikitext = """
    {{Infobox Boss
    |Test Boss Name
    |hp = 50000
    }}
    """

    boss = WikitextParser.parse(wikitext)

    # O nome deve ser extraído do primeiro parâmetro sem nome
    assert boss.name == "Test Boss Name"


def test_parse_boss_name_fallback():
    """Testa que o nome usa fallback quando não encontrado."""
    wikitext = """
    {{Infobox Boss
    |hp = 50000
    }}
    """

    boss = WikitextParser.parse(wikitext, "Fallback Name")

    assert boss.name == "Fallback Name"


def test_parse_boss_case_insensitive_template():
    """Testa que o template é encontrado case-insensitive."""
    wikitext = """
    {{infobox boss
    |hp = 50000
    }}
    """

    boss = WikitextParser.parse(wikitext, "Case Insensitive Boss")

    assert boss.hp == 50000


def test_parse_boss_with_alternative_field_names():
    """Testa parsing com nomes alternativos de campos."""
    wikitext = """
    {{Infobox Boss
    |health = 50000
    |xp = 10000
    |walksthrough = Fire
    |immune = Energy
    }}
    """

    boss = WikitextParser.parse(wikitext, "Alternative Fields Boss")

    assert boss.hp == 50000
    assert boss.exp == 10000
    assert "Fire" in boss.walks_through
    assert "Energy" in boss.immunities


def test_parse_boss_minimal():
    """Testa parsing de boss com apenas nome."""
    wikitext = """
    {{Infobox Boss
    |name = Minimal Boss
    }}
    """

    boss = WikitextParser.parse(wikitext)

    assert boss.name == "Minimal Boss"
    assert boss.hp is None
    assert boss.exp is None
    assert boss.walks_through == []
    assert boss.immunities == []


def test_parse_boss_with_infobox_creature():
    """Testa parsing de boss com template Infobox Creature."""
    wikitext = """
    {{Infobox Creature
    |name = Creature Boss
    |hp = 50000
    |exp = 10000
    |isboss = yes
    }}
    """

    boss = WikitextParser.parse(wikitext, "Creature Boss")

    assert boss.name == "Creature Boss"
    assert boss.hp == 50000
    assert boss.exp == 10000


def test_parse_boss_with_infobox_creature_no_isboss():
    """Testa parsing de boss com Infobox Creature sem campo isboss mas com hp/exp."""
    wikitext = """
    {{Infobox Creature
    |name = Creature Boss 2
    |hp = 30000
    |exp = 5000
    }}
    """

    boss = WikitextParser.parse(wikitext, "Creature Boss 2")

    assert boss.name == "Creature Boss 2"
    assert boss.hp == 30000
    assert boss.exp == 5000

