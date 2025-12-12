"""Testes unitários para BossModel."""

import pytest

from app.models.boss import BossModel


def test_boss_model_basic():
    """Testa criação básica de um BossModel."""
    boss = BossModel(
        name="Test Boss",
        hp=50000,
        exp=10000,
        walks_through=["Fire"],
        immunities=["Energy"],
    )

    assert boss.name == "Test Boss"
    assert boss.hp == 50000
    assert boss.exp == 10000
    assert boss.walks_through == ["Fire"]
    assert boss.immunities == ["Energy"]


def test_boss_model_sanitize_hp_with_commas():
    """Testa sanitização de HP com vírgulas."""
    boss = BossModel(name="Test", hp="50,000")
    assert boss.hp == 50000


def test_boss_model_sanitize_hp_with_estimated():
    """Testa sanitização de HP com (estimated)."""
    boss = BossModel(name="Test", hp="50,000 (estimated)")
    assert boss.hp == 50000


def test_boss_model_sanitize_hp_unknown():
    """Testa sanitização de HP com valores desconhecidos."""
    boss1 = BossModel(name="Test", hp="???")
    assert boss1.hp is None

    boss2 = BossModel(name="Test", hp="Variable")
    assert boss2.hp is None

    boss3 = BossModel(name="Test", hp="unknown")
    assert boss3.hp is None


def test_boss_model_sanitize_exp():
    """Testa sanitização de EXP."""
    boss = BossModel(name="Test", exp="10,000 (estimated)")
    assert boss.exp == 10000

    boss2 = BossModel(name="Test", exp="???")
    assert boss2.exp is None


def test_boss_model_sanitize_walks_through():
    """Testa sanitização de walks_through."""
    boss = BossModel(name="Test", walks_through="Fire, Energy")
    assert boss.walks_through == ["Fire", "Energy"]


def test_boss_model_sanitize_walks_through_with_partial():
    """Testa sanitização de walks_through com (partial)."""
    boss = BossModel(name="Test", walks_through="Fire, Energy (partial)")
    assert boss.walks_through == ["Fire", "Energy"]


def test_boss_model_sanitize_walks_through_none():
    """Testa sanitização de walks_through com None."""
    boss = BossModel(name="Test", walks_through="None")
    assert boss.walks_through == []

    boss2 = BossModel(name="Test", walks_through="")
    assert boss2.walks_through == []


def test_boss_model_sanitize_immunities():
    """Testa sanitização de immunities."""
    boss = BossModel(name="Test", immunities="Fire, Energy, Ice")
    assert boss.immunities == ["Fire", "Energy", "Ice"]


def test_boss_model_sanitize_immunities_list():
    """Testa sanitização de immunities como lista."""
    boss = BossModel(name="Test", immunities=["Fire", "Energy"])
    assert boss.immunities == ["Fire", "Energy"]


def test_boss_model_optional_fields():
    """Testa que campos opcionais podem ser None."""
    boss = BossModel(name="Test Boss")
    assert boss.name == "Test Boss"
    assert boss.hp is None
    assert boss.exp is None
    assert boss.walks_through == []
    assert boss.immunities == []


def test_boss_model_with_int_values():
    """Testa que valores int são aceitos diretamente."""
    boss = BossModel(name="Test", hp=50000, exp=10000)
    assert boss.hp == 50000
    assert boss.exp == 10000

